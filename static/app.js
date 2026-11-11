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
// ── Optimistic UI + Undo Toast (M2) ────────────────────────────────────────
let undoStack = []; // [{type, id, oldNotes, toastId}, ...]
let pendingDeletes = new Set();
let toastQueue = [];
const TOAST_DURATION = 5000;

function showToast(msg, actionLabel) {
  const container = document.getElementById('toastContainer');
  if (!container) {
    const newContainer = document.createElement('div');
    newContainer.id = 'toastContainer';
    newContainer.style.cssText = 'position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 100; display: flex; flex-direction: column; gap: 8px;';
    document.body.appendChild(newContainer);
    container = newContainer;
  }
  const toast = document.createElement('div');
  toast.style.cssText = 'background: var(--fg); color: var(--bg); padding: 10px 16px; border-radius: 8px; font-size: 14px; box-shadow: var(--shadow); display: flex; align-items: center; gap: 10px; animation: toastIn var(--anim-dur) ease-out;';
  toast.innerHTML = `${msg} <span class="undo" style="color: var(--accent); text-decoration: underline; cursor: pointer; margin-left: auto;">${actionLabel || 'Undo'}</span>`;
  container.appendChild(toast);
  toastQueue.push(toast);
  // Auto-dismiss
  const id = setTimeout(() => {
    if (toast.parentNode) toast.parentNode.removeChild(toast);
    toastQueue = toastQueue.filter(t => t !== toast);
    if (toastQueue.length > 0) showNextToast();
    clearTimeout(id);
  }, TOAST_DURATION);
  if (toastQueue.length > 0) setTimeout(showNextToast, TOAST_DURATION + 100);
}
window.notesApp = window.notesApp || {};
window.notesApp.undo = function(id) {
  const entry = undoStack.find(e => e.toastId === id);
  if (!entry) return;
  if (entry.type === 'delete') {
    notes.unshift(entry.note);
  } else if (entry.type === 'add' || entry.type === 'edit') {
    notes = entry.oldNotes;
  }
  renderNotes();
};
function showNextToast() {
  if (toastQueue.length === 0) return;
  const next = toastQueue.shift();
  if (next.parentNode) next.parentNode.removeChild(next);
}
function hideAllToasts() {
  const container = document.getElementById('toastContainer');
  if (container) container.innerHTML = '';
  toastQueue = [];
}

// ── add_note (optimistic) ────────────────────────────────────────────────
// Modify the existing add_note to use optimistic updates
// (the existing function in app.js - need to wrap the fetch part)

// ── delete_note (optimistic) ─────────────────────────────────────────────
// Modify the existing delete_note function

// ── save changes ───────────────────────────────────────────────────────────

// ── Keyboard Shortcuts + FAB (M3) ────────────────────────────────────────
// Skip link focus handler
const skipLink = document.querySelector('a.skip-link');
if (skipLink) {
  skipLink.addEventListener('focus', () => {
    skipLink.style.position = 'fixed';
    skipLink.style.left = '16px';
    skipLink.style.top = '16px';
    skipLink.style.background = 'var(--accent)';
    skipLink.style.color = '#fff';
    skipLink.style.padding = '8px 16px';
    skipLink.style.zIndex = '100';
    skipLink.style.borderRadius = '6px';
  });
  skipLink.addEventListener('blur', () => {
    skipLink.style.position = 'absolute';
    skipLink.style.left = '-999px';
    skipLink.style.width = '1px';
    skipLink.style.height = '1px';
    skipLink.style.overflow = 'hidden';
    skipLink.style.clip = 'rect(1px, 1px, 1px, 1px)';
  });
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // / focus search
  if (e.key === '/') {
    e.preventDefault();
    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.focus();
  }
  // n new note
  if (e.key === 'n' && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
    e.preventDefault();
    const searchInput = document.getElementById('searchInput');
    const tagFilter = document.getElementById('tagFilter');
    if (document.activeElement === searchInput || document.activeElement === tagFilter) {
      // Open editor
      openEditor(null);
    } else {
      searchInput.focus();
    }
  }
  // e edit focused note
  if (e.key === 'e' && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
    e.preventDefault();
    const focusedNote = document.querySelector('.note-card:focus');
    if (focusedNote) {
      const noteId = focusedNote.dataset.id;
      const note = notes.find(n => n.id === noteId);
      if (note) openEditor(note);
    }
  }
  // d delete focused note
  if (e.key === 'd' && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
    e.preventDefault();
    const focusedNote = document.querySelector('.note-card:focus');
    if (focusedNote) {
      const noteId = focusedNote.dataset.id;
      if (confirm('Delete this note?')) {
        // Optimistic delete
        const note = notes.find(n => n.id === noteId);
        if (note) {
          const noteIdx = notes.indexOf(note);
          if (noteIdx > -1) {
            undoStack.push({ type: 'delete', id: note.id, oldNotes: [...notes] });
            pendingDeletes.add(noteId);
            notes = [...notes.slice(0, noteIdx), ...notes.slice(noteIdx + 1)];
            focusedNote.remove();
            renderNotes();
            // Server confirm
            fetch(`${API_BASE}/${noteId}`, { method: 'DELETE' })
              .then(r => r.ok ? undefined : Promise.reject(new Error('Delete failed')))
              .catch(err => {
                pendingDeletes.delete(noteId);
                undoStack.pop();
                const restored = notes.find(n => n.id === noteId);
                if (restored) notes.unshift(restored);
                renderNotes();
                showToast('Delete failed. Undo available.', 'Undo');
              });
          }
        }
      }
    }
  }
});

// FAB click - open editor
const fab = document.getElementById('addFab');
if (fab) {
  fab.addEventListener('click', () => {
    openEditor(null);
  });
}

// Reduced-motion respect for FAB
if (window.matchMedia) {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const fab = document.getElementById('addFab');
  if (fab) {
    if (prefersReducedMotion.matches) {
      fab.style.transition = 'none';
    }
    prefersReducedMotion.addEventListener('change', (e) => {
      if (e.matches) {
        fab.style.transition = 'none';
      } else {
        fab.style.transition = '';
      }
    });
  }
}

// ── Autocomplete suggest (M6) ────────────────────────────────────────────
let acTimer = null;
let acResults = [];
let acVisible = false;
let acSelectedIdx = -1;

function showAcResults(results) {
  const acContainer = document.getElementById('acContainer');
  const acDropdown = document.getElementById('acDropdown');
  const acEmpty = document.getElementById('acEmpty');
  const searchInput = document.getElementById('searchInput');
  if (!acContainer || !acDropdown || !acEmpty || !searchInput) return;

  acVisible = true;
  acResults = results;

  if (!results || results.length === 0) {
    acDropdown.hidden = true;
    acEmpty.hidden = false;
    acContainer.style.display = 'block';
    searchInput.setAttribute('aria-expanded', 'false');
    searchInput.removeAttribute('aria-activedescendant');
    return;
  }

  acDropdown.hidden = false;
  acEmpty.hidden = true;
  acContainer.style.display = 'block';
  searchInput.setAttribute('aria-expanded', 'true');

  let itemsHtml = '';
  results.forEach((s, i) => {
    const type = s.type;
    const highlight = s.highlight || s.value;
    const selected = i === acSelectedIdx ? ' ac-selected' : '';
    itemsHtml += `<div class="ac-item${selected}" data-type="${type}" data-index="${i}" role="option" role="option" tabindex="0" aria-selected="${i === acSelectedIdx}" style="user-select:none;">
      ${highlight}
    </div>`;
  });
  acDropdown.innerHTML = `<div class="ac-content">${itemsHtml}</div>`;
  searchInput.setAttribute('aria-activedescendant', acSelectedIdx >= 0 ? `acItem-${acSelectedIdx}` : null);
}

function hideAc() {
  const acContainer = document.getElementById('acContainer');
  if (acContainer) {
    acDropdown.hidden = true;
    acEmpty.hidden = true;
    acContainer.style.display = 'none';
    acVisible = false;
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
      searchInput.setAttribute('aria-expanded', 'false');
      searchInput.removeAttribute('aria-activedescendant');
    }
  }
}

function handleAcKeydown(e) {
  if (!acVisible) return;
  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault();
      acSelectedIdx = Math.min(acSelectedIdx + 1, acResults.length - 1);
      showAcResults(acResults);
      break;
    case 'ArrowUp':
      e.preventDefault();
      acSelectedIdx = Math.max(acSelectedIdx - 1, -1);
      showAcResults(acResults);
      break;
    case 'Escape':
      e.preventDefault();
      hideAc();
      break;
    case 'Enter':
      e.preventDefault();
      if (acSelectedIdx >= 0 && acResults.length > 0) {
        const selected = acResults[acSelectedIdx];
        const searchInput = document.getElementById('searchInput');
        if (searchInput) searchInput.value = selected.value;
        hideAc();
      } else {
        hideAc();
      }
      break;
  }
}

// Attach autocomplete logic after search input is available
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchInput');
  if (!searchInput) return;

  const debounce = (fn, ms) => {
    let timer;
    return function () {
      clearTimeout(timer);
      timer = setTimeout(fn, ms);
    };
  };

  searchInput.addEventListener('input', (e) => {
    clearTimeout(acTimer);
    const query = e.target.value.trim();
    acTimer = setTimeout(() => {
      if (!query || query.length < 1) {
        hideAc();
        return;
      }
      fetch(`/api/notes/suggest?q=${encodeURIComponent(query)}`)
        .then(res => {
          if (!res.ok) throw new Error('Suggest failed');
          return res.json();
        })
        .then(data => {
          showAcResults(data.suggestions || []);
        })
        .catch(err => {
          console.error('Autocomplete error:', err);
          hideAc();
        });
    }, 200);
  });

  document.addEventListener('click', (e) => {
    const target = e.target;
    if (acVisible && target !== searchInput && !target.closest('#acContainer')) {
      hideAc();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (acVisible && e.key === 'Escape') {
      hideAc();
    }
  });
});
