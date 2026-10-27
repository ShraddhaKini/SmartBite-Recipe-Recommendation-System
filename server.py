from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, re, traceback

try:
    import joblib
    import pandas as pd
except ImportError:
    joblib = pd = None

HERE = Path(__file__).resolve().parent
MODEL_PATH = HERE / 'smartbite_best_model.joblib'
RECIPES_PATH = HERE / 'recipes_for_website.json'
PACKAGE = None
RECIPES = None

# Conservative keyword rules. Recipe tags are not trusted as the sole proof of diet.
MEAT_TERMS = {
 'chicken','turkey','duck','goose','quail','beef','pork','bacon','ham','lamb','mutton','goat meat','veal','venison','rabbit',
 'sausage','pepperoni','salami','prosciutto','meat','poultry','fish','salmon','tuna','anchovy','sardine','mackerel','cod','trout',
 'tilapia','prawn','shrimp','crab','lobster','clam','mussel','oyster','scallop','squid','octopus','seafood','fish sauce',
 'oyster sauce','shrimp paste','anchovy paste','chicken stock','beef stock','bone broth','meat broth','lard','gelatin','isinglass'
}
ANIMAL_TERMS = MEAT_TERMS | {'egg','eggs','milk','butter','cheese','cream','yogurt','yoghurt','ghee','whey','casein','honey','mayonnaise','mayo','buttermilk','paneer','condensed milk','evaporated milk'}

def norm(x): return re.sub(r'[^a-z0-9]+', ' ', str(x or '').lower()).strip()
def listify(x):
    if isinstance(x, list): return [str(v) for v in x if v is not None]
    if isinstance(x, str):
        try:
            v=json.loads(x)
            if isinstance(v,list): return [str(i) for i in v if i is not None]
        except (json.JSONDecodeError, TypeError): pass
        return [x] if x.strip() else []
    return []
def contains_any(text, terms):
    n=f' {norm(text)} '
    return any(f' {norm(t)} ' in n for t in terms)
def tags_of(r): return [norm(t) for t in listify(r.get('tags'))]
def has_nonveg_tag(tags):
    return any('non vegetarian' in t or 'nonvegetarian' in t or ('meat' in t and 'meatless' not in t) for t in tags)
def is_vegetarian(r):
    ingredients=listify(r.get('ingredients')); tags=tags_of(r)
    if any(contains_any(i, MEAT_TERMS) for i in ingredients): return False
    if has_nonveg_tag(tags): return False
    return True
def is_vegan(r):
    ingredients=listify(r.get('ingredients'))
    if any(contains_any(i, ANIMAL_TERMS) for i in ingredients): return False
    return not has_nonveg_tag(tags_of(r))
def is_nonvegetarian(r):
    ingredients=listify(r.get('ingredients')); tags=tags_of(r)
    return any(contains_any(i, MEAT_TERMS) for i in ingredients) or has_nonveg_tag(tags)
def matches_ingredients(requested, ingredients):
    normalized=[norm(x) for x in ingredients]; matched=[]
    for q in requested:
        if any(q == ing or f' {q} ' in f' {ing} ' or f' {ing} ' in f' {q} ' for ing in normalized if ing): matched.append(q)
    return list(dict.fromkeys(matched))
def load_data():
    global PACKAGE, RECIPES
    if RECIPES is None:
        if not RECIPES_PATH.exists(): raise FileNotFoundError('recipes_for_website.json is missing. Export it from Phase 3 in Colab and place it beside server.py.')
        raw=json.loads(RECIPES_PATH.read_text(encoding='utf-8'))
        if isinstance(raw,dict): raw=raw.get('recipes',raw.get('data',[]))
        if not isinstance(raw,list): raise ValueError('recipes_for_website.json must contain a list of recipe objects.')
        RECIPES=raw
    if PACKAGE is None and MODEL_PATH.exists() and joblib is not None:
        try: PACKAGE=joblib.load(MODEL_PATH)
        except Exception as e: print('Warning: ML model unavailable; recommendations will use ingredient matching only:',e); PACKAGE={}
    return PACKAGE or {}, RECIPES
def ml_signal(r, package):
    if not isinstance(package,dict) or 'model' not in package or pd is None: return None,0.0
    try:
        features=package.get('feature_names',['minutes','n_steps','n_ingredients'])
        steps=listify(r.get('steps') or r.get('instructions')); ingredients=listify(r.get('ingredients'))
        values={'minutes':max(1,float(r.get('minutes') or 1)),'n_steps':max(1,float(r.get('n_steps') or len(steps) or 1)),'n_ingredients':max(1,float(r.get('n_ingredients') or len(ingredients) or 1))}
        row=pd.DataFrame([[values.get(f,1) for f in features]],columns=features)
        if package.get('uses_scaling') and package.get('scaler') is not None: row=package['scaler'].transform(row)
        model=package['model']; pred=int(model.predict(row)[0]); prob=float(model.predict_proba(row)[0][1]) if hasattr(model,'predict_proba') else float(pred)
        return ('Likely high rating' if pred==1 else 'Likely lower rating'),prob
    except Exception as e:
        print('Skipping ML score for recipe:',e); return None,0.0
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(HERE),**kwargs)
    def send_json(self,obj,status=200):
        b=json.dumps(obj,ensure_ascii=False).encode('utf-8'); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        if self.path!='/recommend': self.send_error(404); return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<=0 or size>100000: return self.send_json({'error':'Invalid request size.'},400)
            payload=json.loads(self.rfile.read(size).decode('utf-8'))
            requested=list(dict.fromkeys(norm(x) for x in listify(payload.get('ingredients')) if norm(x)))
            if not requested: return self.send_json({'error':'Enter at least one ingredient.'},400)
            if len(requested)>30: return self.send_json({'error':'Enter up to 30 ingredients.'},400)
            diet=str(payload.get('diet','any')).lower()
            if diet not in {'any','vegetarian','vegan','non_vegetarian'}: return self.send_json({'error':'Invalid diet preference.'},400)
            min_matches=max(1,min(10,int(payload.get('min_matches',2))))
            max_time=max(0,int(payload.get('max_time',0) or 0))
            package,recipes=load_data(); candidates=[]
            for r in recipes:
                if not isinstance(r,dict): continue
                try: minutes=max(0,int(float(r.get('minutes') or 0)))
                except (ValueError,TypeError): minutes=0
                if max_time and (minutes==0 or minutes>max_time): continue
                # Diet filters are applied before ingredient matching and ranking.
                if diet=='vegetarian' and not is_vegetarian(r): continue
                if diet=='vegan' and not is_vegan(r): continue
                if diet=='non_vegetarian' and not is_nonvegetarian(r): continue
                ingredients=listify(r.get('ingredients')); matched=matches_ingredients(requested,ingredients)
                if len(matched)<min_matches: continue
                label,prob=ml_signal(r,package)
                score=len(matched)+(prob*0.2 if label else 0.0)
                candidates.append({'name':str(r.get('name') or r.get('title') or 'Recipe'),'minutes':minutes,'match_count':len(matched),'matched':matched,'ingredients':ingredients,'steps':listify(r.get('steps') or r.get('instructions')),'ml_label':label,'_score':score})
            candidates.sort(key=lambda x:(x['_score'],x['match_count']),reverse=True)
            total=len(candidates)
            for r in candidates: r.pop('_score',None)
            return self.send_json({'results':candidates[:12],'total_matches':total})
        except FileNotFoundError as e: return self.send_json({'error':str(e)},500)
        except (json.JSONDecodeError,ValueError,TypeError) as e: return self.send_json({'error':f'Invalid request or recipe data: {e}'},400)
        except Exception:
            traceback.print_exc(); return self.send_json({'error':'Unexpected server error. See Command Prompt for details.'},500)
    def log_message(self,fmt,*args): print('%s - %s'%(self.address_string(),fmt%args))
if __name__=='__main__':
    print('SmartBite starting at http://127.0.0.1:8000')
    print('Required: recipes_for_website.json beside server.py. Model file is optional.')
    ThreadingHTTPServer(('127.0.0.1',8000),Handler).serve_forever()
