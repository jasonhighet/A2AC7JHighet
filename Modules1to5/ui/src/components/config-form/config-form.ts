/**
 * src/components/config-form/config-form.ts
 * -------------------------------------------
 * Modal form for creating and editing configurations.
 * Includes a raw textarea JSON editor for the `config` field.
 *
 * Public API:
 *   - resetForApp(appId: string) — clears form for a new config under appId
 *   - loadConfig(config)         — prefills form for editing an existing config
 *
 * Emitted events (bubble + composed):
 *   - 'form-close'    → no detail
 *   - 'form-success'  → detail: string  (success message)
 */

import { store } from '../../store/app-store.js';
import type { ConfigurationResponse } from '../../api/types.js';

const template = document.createElement('template');
template.innerHTML = `
  <style>
    :host { display: block; }

    .card {
      background: var(--color-bg-surface);
      border: var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: var(--space-8);
      width: 560px;
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
    }

    input:focus, textarea:focus {
      outline: none;
      border-color: var(--color-accent);
      box-shadow: 0 0 0 3px var(--color-accent-subtle);
    }

    .json-editor {
      font-family: var(--font-family-mono);
      font-size: var(--font-size-sm);
      min-height: 160px;
      resize: vertical;
      line-height: 1.5;
    }

    .json-hint {
      font-size: var(--font-size-xs);
      color: var(--color-text-muted);
      margin-top: var(--space-1);
    }

    .json-hint.invalid { color: var(--color-error); }

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

    .btn-cancel { background: var(--color-bg-elevated); color: var(--color-text-muted); border: var(--border-subtle); }
    .btn-cancel:hover { color: var(--color-text-primary); }
    .btn-submit { background: var(--color-accent); color: var(--color-text-inverse); }
    .btn-submit:hover { background: var(--color-accent-hover); transform: translateY(-1px); }
    .btn-submit:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

    .error { font-size: var(--font-size-sm); color: var(--color-error); margin-top: var(--space-3); display: none; }
    .error.visible { display: block; }
  </style>

  <div class="card">
    <h2 id="formTitle">New Configuration</h2>
    <form id="form" novalidate>
      <div class="field">
        <label for="name">Name <span style="color:var(--color-error)">*</span></label>
        <input id="name" type="text" placeholder="e.g. production" required autocomplete="off" />
      </div>
      <div class="field">
        <label for="comments">Comments</label>
        <input id="comments" type="text" placeholder="Optional description…" />
      </div>
      <div class="field">
        <label for="configJson">Config (JSON) <span style="color:var(--color-error)">*</span></label>
        <textarea id="configJson" class="json-editor" placeholder='{\n  "key": "value"\n}'>{}</textarea>
        <p class="json-hint" id="jsonHint">Enter a valid JSON object.</p>
      </div>
      <p class="error" id="errorMsg"></p>
      <div class="actions">
        <button type="button" class="btn btn-cancel" id="cancelBtn">Cancel</button>
        <button type="submit" class="btn btn-submit" id="submitBtn">Create</button>
      </div>
    </form>
  </div>
`;

export class ConfigForm extends HTMLElement {
    #shadow: ShadowRoot;
    #editId: string | null = null;
    #appId: string | null = null;

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
        const jsonEditor = this.#shadow.getElementById('configJson') as HTMLTextAreaElement;
        jsonEditor.addEventListener('input', () => this.#validateJson());
    }

    resetForApp(appId: string): void {
        this.#editId = null;
        this.#appId = appId;
        (this.#shadow.getElementById('name') as HTMLInputElement).value = '';
        (this.#shadow.getElementById('comments') as HTMLInputElement).value = '';
        (this.#shadow.getElementById('configJson') as HTMLTextAreaElement).value = '{}';
        (this.#shadow.getElementById('formTitle') as HTMLElement).textContent = 'New Configuration';
        (this.#shadow.getElementById('submitBtn') as HTMLButtonElement).textContent = 'Create';
        this.#clearError();
        this.#validateJson();
    }

    loadConfig(config: ConfigurationResponse): void {
        this.#editId = config.id;
        this.#appId = config.application_id;
        (this.#shadow.getElementById('name') as HTMLInputElement).value = config.name;
        (this.#shadow.getElementById('comments') as HTMLInputElement).value = config.comments ?? '';
        (this.#shadow.getElementById('configJson') as HTMLTextAreaElement).value =
            JSON.stringify(config.config, null, 2);
        (this.#shadow.getElementById('formTitle') as HTMLElement).textContent = 'Edit Configuration';
        (this.#shadow.getElementById('submitBtn') as HTMLButtonElement).textContent = 'Save Changes';
        this.#clearError();
        this.#validateJson();
    }

    #validateJson(): boolean {
        const raw = (this.#shadow.getElementById('configJson') as HTMLTextAreaElement).value.trim();
        const hint = this.#shadow.getElementById('jsonHint')!;
        try {
            const parsed = JSON.parse(raw) as unknown;
            if (typeof parsed !== 'object' || Array.isArray(parsed) || parsed === null) {
                hint.textContent = 'Must be a JSON object (not an array or null).';
                hint.classList.add('invalid');
                return false;
            }
            hint.textContent = '✓ Valid JSON object.';
            hint.classList.remove('invalid');
            return true;
        } catch {
            hint.textContent = 'Invalid JSON — check for missing commas or quotes.';
            hint.classList.add('invalid');
            return false;
        }
    }

    #close(): void {
        this.dispatchEvent(new CustomEvent('form-close', { bubbles: true, composed: true }));
    }

    async #submit(): Promise<void> {
        const name = (this.#shadow.getElementById('name') as HTMLInputElement).value.trim();
        if (!name) { this.#showError('Name is required.'); return; }
        if (!this.#validateJson()) { this.#showError('Fix the JSON before saving.'); return; }
        if (!this.#appId) { this.#showError('No application selected.'); return; }

        const raw = (this.#shadow.getElementById('configJson') as HTMLTextAreaElement).value.trim();
        const config = JSON.parse(raw) as Record<string, unknown>;
        const comments = (this.#shadow.getElementById('comments') as HTMLInputElement).value.trim();
        const submitBtn = this.#shadow.getElementById('submitBtn') as HTMLButtonElement;
        submitBtn.disabled = true;
        this.#clearError();

        let result;
        if (this.#editId) {
            result = await store.updateConfiguration(this.#editId, {
                name, config, comments: comments || undefined,
            });
        } else {
            result = await store.createConfiguration({
                application_id: this.#appId,
                name, config, comments: comments || undefined,
            });
        }

        submitBtn.disabled = false;

        if (result) {
            const msg = this.#editId
                ? `Configuration "${result.name}" updated.`
                : `Configuration "${result.name}" created.`;
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

customElements.define('config-form', ConfigForm);
