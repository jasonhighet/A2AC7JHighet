/**
 * src/components/app-form/app-form.ts
 * -------------------------------------
 * Modal form for creating and editing applications.
 *
 * Public API (called by app-shell):
 *   - reset()           — clears the form for creating a new application
 *   - loadApp(app)      — prefills the form for editing an existing application
 *
 * Emitted events (bubble + composed):
 *   - 'form-close'    → no detail  (user clicked Cancel)
 *   - 'form-success'  → detail: string  (success message, handled by app-shell for toast)
 */

import { store } from '../../store/app-store.js';
import type { ApplicationResponse } from '../../api/types.js';

const template = document.createElement('template');
template.innerHTML = `
  <style>
    :host { display: block; }

    .card {
      background: var(--color-bg-surface);
      border: var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: var(--space-8);
      width: 460px;
      max-width: 90vw;
      box-shadow: var(--shadow-modal);
      animation: slide-in var(--transition-normal) ease;
    }

    @keyframes slide-in {
      from { opacity: 0; transform: translateY(-12px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    h2 {
      font-size: var(--font-size-lg);
      font-weight: var(--font-weight-semibold);
      color: var(--color-text-primary);
      margin-bottom: var(--space-6);
    }

    .field { margin-bottom: var(--space-4); }

    label {
      display: block;
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      color: var(--color-text-muted);
      margin-bottom: var(--space-2);
    }

    input, textarea {
      width: 100%;
      padding: var(--space-3);
      background: var(--color-bg-elevated);
      border: var(--border-subtle);
      border-radius: var(--radius-md);
      color: var(--color-text-primary);
      font-size: var(--font-size-base);
      font-family: var(--font-family-base);
      transition: border-color var(--transition-fast);
      box-sizing: border-box;
      resize: vertical;
    }

    input:focus, textarea:focus {
      outline: none;
      border-color: var(--color-accent);
      box-shadow: 0 0 0 3px var(--color-accent-subtle);
    }

    textarea { min-height: 80px; }

    .actions {
      display: flex;
      gap: var(--space-3);
      justify-content: flex-end;
      margin-top: var(--space-6);
    }

    .btn {
      padding: var(--space-2) var(--space-5);
      border-radius: var(--radius-md);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-semibold);
      font-family: var(--font-family-base);
      cursor: pointer;
      transition: background var(--transition-fast), transform var(--transition-fast);
      border: none;
    }

    .btn-cancel {
      background: var(--color-bg-elevated);
      color: var(--color-text-muted);
      border: var(--border-subtle);
    }
    .btn-cancel:hover { color: var(--color-text-primary); }

    .btn-submit {
      background: var(--color-accent);
      color: var(--color-text-inverse);
    }
    .btn-submit:hover { background: var(--color-accent-hover); transform: translateY(-1px); }
    .btn-submit:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

    .error {
      font-size: var(--font-size-sm);
      color: var(--color-error);
      margin-top: var(--space-3);
      display: none;
    }
    .error.visible { display: block; }
  </style>

  <div class="card">
    <h2 id="formTitle">New Application</h2>
    <form id="form" novalidate>
      <div class="field">
        <label for="name">Name <span style="color:var(--color-error)">*</span></label>
        <input id="name" type="text" placeholder="e.g. payments-service" required autocomplete="off" />
      </div>
      <div class="field">
        <label for="comments">Comments</label>
        <textarea id="comments" placeholder="Optional description…"></textarea>
      </div>
      <p class="error" id="errorMsg"></p>
      <div class="actions">
        <button type="button" class="btn btn-cancel" id="cancelBtn">Cancel</button>
        <button type="submit" class="btn btn-submit" id="submitBtn">Create</button>
      </div>
    </form>
  </div>
`;

export class AppForm extends HTMLElement {
    #shadow: ShadowRoot;
    #editId: string | null = null;

    constructor() {
        super();
        this.#shadow = this.attachShadow({ mode: 'open' });
        this.#shadow.appendChild(template.content.cloneNode(true));
    }

    connectedCallback(): void {
        this.#shadow.getElementById('cancelBtn')!.addEventListener('click', () => this.#close());
        this.#shadow.getElementById('form')!.addEventListener('submit', (e) => {
            e.preventDefault();
            void this.#submit();
        });
    }

    /** Prepare the form for creating a new application. */
    reset(): void {
        this.#editId = null;
        (this.#shadow.getElementById('name') as HTMLInputElement).value = '';
        (this.#shadow.getElementById('comments') as HTMLTextAreaElement).value = '';
        (this.#shadow.getElementById('formTitle') as HTMLElement).textContent = 'New Application';
        (this.#shadow.getElementById('submitBtn') as HTMLButtonElement).textContent = 'Create';
        this.#clearError();
    }

    /** Prefill the form for editing an existing application. */
    loadApp(app: ApplicationResponse): void {
        this.#editId = app.id;
        (this.#shadow.getElementById('name') as HTMLInputElement).value = app.name;
        (this.#shadow.getElementById('comments') as HTMLTextAreaElement).value = app.comments ?? '';
        (this.#shadow.getElementById('formTitle') as HTMLElement).textContent = 'Edit Application';
        (this.#shadow.getElementById('submitBtn') as HTMLButtonElement).textContent = 'Save Changes';
        this.#clearError();
    }

    #close(): void {
        this.dispatchEvent(new CustomEvent('form-close', { bubbles: true, composed: true }));
    }

    async #submit(): Promise<void> {
        const name = (this.#shadow.getElementById('name') as HTMLInputElement).value.trim();
        if (!name) { this.#showError('Name is required.'); return; }

        const comments = (this.#shadow.getElementById('comments') as HTMLTextAreaElement).value.trim();
        const submitBtn = this.#shadow.getElementById('submitBtn') as HTMLButtonElement;
        submitBtn.disabled = true;
        this.#clearError();

        let result;
        if (this.#editId) {
            result = await store.updateApplication(this.#editId, { name, comments: comments || undefined });
        } else {
            result = await store.createApplication({ name, comments: comments || undefined });
        }

        submitBtn.disabled = false;

        if (result) {
            const msg = this.#editId ? `Application "${result.name}" updated.` : `Application "${result.name}" created.`;
            this.dispatchEvent(new CustomEvent('form-success', { detail: msg, bubbles: true, composed: true }));
        } else if (store.error) {
            this.#showError(store.error);
        }
    }

    #showError(msg: string): void {
        const el = this.#shadow.getElementById('errorMsg')!;
        el.textContent = msg;
        el.classList.add('visible');
    }

    #clearError(): void {
        const el = this.#shadow.getElementById('errorMsg')!;
        el.textContent = '';
        el.classList.remove('visible');
    }
}

customElements.define('app-form', AppForm);
