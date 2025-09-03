// static/script.js

// Tab handling
document.addEventListener('DOMContentLoaded', () => {
  const tabs = Array.from(document.querySelectorAll('.tab'));
  const cards = document.querySelectorAll('.card');

  function showClass(cls){
    // if overall: show all overall cards (we only render overall on page)
    if(cls === 'overall'){
      cards.forEach(c => c.style.display = 'flex');
    } else {
      cards.forEach(c => {
        // each card has data-classes attribute, but current template renders only overall cards
        // keep for compatibility if per-class rendering is added client-side
        c.style.display = c.dataset.classes && c.dataset.classes.split(' ').includes(cls) ? 'flex' : 'none';
      });
    }
  }

  tabs.forEach(t => t.addEventListener('click', () => {
    tabs.forEach(x => x.classList.remove('active'));
    t.classList.add('active');
    showClass(t.dataset.class);
  }));

  // file upload: read HTML and extract table, then POST JSON to /update
  const fileUpload = document.getElementById('fileUpload');
  if (fileUpload) {
    fileUpload.addEventListener('change', async (ev) => {
      const file = ev.target.files[0];
      if (!file) return;
      const text = await file.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(text, 'text/html');
      const table = doc.querySelector('table');
      if (!table) { alert('No table found in uploaded HTML.'); return; }
      const rows = Array.from(table.querySelectorAll('tr')).slice(1);
      const entries = [];
      rows.forEach(row => {
        const cells = row.querySelectorAll('td, th');
        if (cells.length >= 2) {
          const name = cells[0].innerText.trim();
          const grade = parseFloat(cells[1].innerText.trim());
          const weight = cells.length > 2 ? parseFloat(cells[2].innerText.trim()) : 1;
          const cls = cells.length > 3 ? cells[3].innerText.trim() : 'General';
          if (!isNaN(grade)) entries.push({name, grade, weight, class: cls});
        }
      });
      if (!entries.length) { alert('No valid rows detected.'); return; }
      try {
        const resp = await fetch('/update', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(entries)
        });
        if (resp.ok) {
          alert('Grades uploaded and leaderboard updated.');
          location.reload();
        } else {
          alert('Upload failed (server).');
        }
      } catch (e) {
        alert('Upload failed: ' + e);
      }
    });
  }

  // Bookmarklet installation link: create code, show via href
  const bookmarkletLink = document.getElementById('bookmarkletLink');
  if (bookmarkletLink) {
    const server = window.location.origin; // use deployed origin by default
    const code = `
javascript:(function(){
  try{
    let rows=document.querySelectorAll('table tr');let data=[];
    for(let i=1;i<rows.length;i++){let cells=rows[i].querySelectorAll('td,th');
      if(cells.length>=2){let name=cells[0].innerText.trim();let grade=parseFloat(cells[1].innerText.trim());
        let weight=cells.length>2?parseFloat(cells[2].innerText.trim()):1;let cls=cells.length>3?cells[3].innerText.trim():'General';
        if(!isNaN(grade))data.push({name,grade,weight,class:cls});}}
    fetch('${server}/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
      .then(r=>r.ok?alert('Grades uploaded successfully!'):alert('Upload failed'))
      .catch(e=>alert('Upload failed: '+e));
  }catch(e){alert('Error: '+e);}
})();`.trim();
    bookmarkletLink.href = code;
    bookmarkletLink.title = "Drag this link to your bookmarks bar or right-click -> Bookmark this link";
  }
});
