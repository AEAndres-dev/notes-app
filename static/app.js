const API_BASE = '/api/notes';

const notesList = document.getElementById('notesList');
const emptyState = document.getElementById('emptyState');
const searchInput = document.getElementById('searchInput');
const tagFilter = document.getElementById('tagFilter');
const addForm = document.getElementById('addForm');
const formError = document.getElementById('formError');

let notes = [];
let debounceTimer;

async function loadNotes() {
  const params = new URLSearchParams();
  const tag = tagFilter.value.trim();
  const q = searchInput.value.trim();
  if (tag) params.set('tag', tag);
  if (q) params.set('q', q);

  const url = API_BASE + (params.toString() ? '?' + params.toString() : '');
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to load notes');
  notes = await res.json();
  renderNotes();
}

function renderNotes() {
  notesList.innerHTML = '';
  if (notes.length === 0) {
    emptyState.classList.remove('hidden');
    notesList.classList.add('hidden');
    return;
  }
  emptyState.classList.add('hidden');
  notesList.classList.remove('hidden');

  for (const note of notes) {
    notesList.appendChild(createNoteCard(note));
  }
}

function createNoteCard(note) {
  const card = document.createElement('article');
  card.className = 'card note-card';
  card.dataset.id = note.id;

  const tagsHtml = (note.tags || []).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('');

  card.innerHTML = `
    <div class="note-header">
      <h3 class="note-title">${escapeHtml(note.title)}</h3>
      <button class="btn btn-edit">Edit</button>
      <button class="btn btn-delete">Delete</button>
    </div>
    <div class="note-body">${escapeHtml(note.body)}</div>
    <div class="note-tags">${tagsHtml}</div>
    <div class="note-edit hidden">
      <div class="field">
        <input type="text" class="edit-title" value="${escapeHtmlAttr(note.title)}" maxlength="200">
      </div>
      <div class="field">
        <textarea class="edit-body" rows="3" maxlength="10000">${escapeHtmlAttr(note.body)}</textarea>
      </div>
      <div class="field">
        <input type="text" class="edit-tags" value="${escapeHtmlAttr((note.tags || []).join(', '))}" placeholder="tags">
      </div>
      <div class="edit-actions">
        <button class="btn btn-save">Save</button>
        <button class="btn btn-cancel">Cancel</button>
      </div>
      <p class="edit-error error-msg"></p>
    </div>
  `;

  const editBtn = card.querySelector('.btn-edit');
  const cancelBtn = card.querySelector('.btn-cancel');
  const saveBtn = card.querySelector('.btn-save');
  const deleteBtn = card.querySelector('.btn-delete');
  const editSection = card.querySelector('.note-edit');
  const editError = card.querySelector('.edit-error');

  editBtn.onclick = () => {
    editSection.classList.remove('hidden');
    editBtn.classList.add('hidden');
    editError.textContent = '';
  };

  cancelBtn.onclick = () => {
    editSection.classList.add('hidden');
    editBtn.classList.remove('hidden');
    editError.textContent = '';
  };

  deleteBtn.onclick = async () => {
    if (!confirm('Delete this note?')) return;
    try {
      const res = await fetch(`${API_BASE}/${note.id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Delete failed');
      notes = notes.filter(n => n.id !== note.id);
      renderNotes();
    } catch (err) {
      alert('Failed to delete note: ' + err.message);
    }
  };

  saveBtn.onclick = async () => {
    const titleInput = card.querySelector('.edit-title');
    const bodyInput = card.querySelector('.edit-body');
    const tagsInput = card.querySelector('.edit-tags');

    const updates = {};
    const newTitle = titleInput.value.trim();
    const newBody = bodyInput.value.trim();
    if (newTitle !== note.title) updates.title = newTitle;
    if (newBody !== note.body) updates.body = newBody;

    const tagsRaw = tagsInput.value.trim();
    const newTags = tagsRaw ? tagsRaw.split(',').map(t => t.trim()).filter(t => t) : [];
    if (JSON.stringify(newTags) !== JSON.stringify(note.tags || [])) updates.tags = newTags;

    if (Object.keys(updates).length === 0) {
      editSection.classList.add('hidden');
      editBtn.classList.remove('hidden');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/${note.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      if (!res.ok) {
        const err = await res.json();
        editError.textContent = err.error || 'Update failed';
        return;
      }
      const updated = await res.json();
      const idx = notes.findIndex(n => n.id === note.id);
      if (idx !== -1) notes[idx] = updated;
      renderNotes();
    } catch (err) {
      editError.textContent = 'Update failed: ' + err.message;
    }
  };

  return card;
}

async function handleAdd(e) {
  e.preventDefault();
  formError.textContent = '';

  const title = document.getElementById('titleInput').value.trim();
  const body = document.getElementById('bodyInput').value.trim();
  const tagsRaw = document.getElementById('tagsInput').value.trim();
  const tags = tagsRaw ? tagsRaw.split(',').map(t => t.trim()).filter(t => t) : [];

  if (!title) {
    formError.textContent = 'Title is required';
    return;
  }

  try {
    const res = await fetch(API_BASE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, body, tags })
    });
    if (!res.ok) {
      const err = await res.json();
      formError.textContent = err.error || 'Add failed';
      return;
    }
    const created = await res.json();
    notes.unshift(created);
    renderNotes();
    addForm.reset();
  } catch (err) {
    formError.textContent = 'Add failed: ' + err.message;
  }
}

function debounce(fn, ms) {
  return function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(fn, ms);
  };
}

function escapeHtml(text) {
  if (text == null) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function escapeHtmlAttr(text) {
  return escapeHtml(text).replace(/"/g, '&quot;');
}

// Wire up
addForm.onsubmit = handleAdd;
searchInput.oninput = debounce(loadNotes, 300);
tagFilter.oninput = debounce(loadNotes, 300);

loadNotes().catch(err => {
  console.error(err);
  formError.textContent = 'Failed to load notes';
});