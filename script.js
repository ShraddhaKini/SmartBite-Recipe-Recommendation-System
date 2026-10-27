const $ = id => document.getElementById(id);
const input = $('ingredients'), button = $('find'), results = $('results'), count = $('count');
button.addEventListener('click', recommend);
input.addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') recommend(); });
async function recommend() {
  const ingredients = input.value.split(',').map(s => s.trim()).filter(Boolean);
  if (!ingredients.length) { message('Please enter at least one ingredient.', true); count.textContent = ''; input.focus(); return; }
  button.disabled = true; button.textContent = 'Finding recipes…';
  try {
    const response = await fetch('/recommend', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ingredients, diet:$('diet').value, max_time:Number($('maxtime').value), min_matches:Number($('minmatch').value)})});
    const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Recommendation request failed');
    count.textContent = `${data.total_matches} matching recipe${data.total_matches === 1 ? '' : 's'}`;
    if (!data.results.length) { message('No recipes matched all selected filters. Try lowering minimum matches or increasing cooking time.', false); return; }
    results.replaceChildren(...data.results.map(card));
  } catch (e) { message(`${e.message}. Check that server.py is running and recipes_for_website.json is beside it.`, true); count.textContent = ''; }
  finally { button.disabled = false; button.textContent = 'Recommend recipes →'; }
}
function card(r) {
  const a=document.createElement('article'); a.className='recipe'; const h=document.createElement('h3'); h.textContent=r.name || 'Recipe'; a.append(h);
  const meta=document.createElement('div'); meta.className='meta'; meta.append(pill(`⏱ ${r.minutes} min`),pill(`${r.match_count} ingredient matches`)); if(r.ml_label)meta.append(pill(r.ml_label)); a.append(meta);
  paragraph(a,'Matched: ',(r.matched||[]).join(', ')); paragraph(a,'Ingredients: ',(r.ingredients||[]).join(', '));
  const d=document.createElement('details'),s=document.createElement('summary');s.textContent='View cooking steps';d.append(s);
  if((r.steps||[]).length){const ol=document.createElement('ol');r.steps.forEach(x=>{const li=document.createElement('li');li.textContent=x;ol.append(li)});d.append(ol)}else{const p=document.createElement('p');p.textContent='Cooking steps are not available.';d.append(p)}a.append(d);return a;
}
function paragraph(parent,label,value){const p=document.createElement('p'),b=document.createElement('b');b.textContent=label;p.append(b,document.createTextNode(value||'Not available'));parent.append(p)}
function pill(t){const s=document.createElement('span');s.className='pill';s.textContent=t;return s}
function message(t,err){const p=document.createElement('p');p.className=err?'error':'empty';p.textContent=t;results.replaceChildren(p)}
