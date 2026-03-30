/**
 * src/components/config-list/config-list.ts
 * -------------------------------------------
 * Renders the list of configurations for the selected application.
 *
 * Observed attributes: none
 * Emitted events (bubble + composed):
 *   - 'edit-config'  →  detail: ConfigurationResponse
 * Store subscriptions: configs-changed, app-selected
 */

import { store } from '../../store/app-store.js';
import type { ConfigurationResponse } from '../../api/types.js';

const template = document.createElement('template');
template.innerHTML = `
  <style>
    :host { display: block; }

    .empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: var(--space-12) var(--space-8);
      color: var(--color-text-muted);
      text-align: center;
      gap: var(--space-3);
    }

    .empty-icon { font-size: 2.5rem; opacity: 0.4; }
    .empty-title { font-size: var(--font-size-lg); color: var(--color-text-primary); font-weight: var(--font-weight-medium); }
    .empty-sub { font-size: var(--font-size-sm); }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: var(--space-4);
    }

    .card {
      background: var(--color-bg-surface);
      border: var(--border-subtle);
      border-radius: var(--radius-md);
      padding: var(--space-5);
      transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
      cursor: default;
    }

    .card:hover {
      border-color: rgba(255,255,255,0.15);
      box-shadow: var(--shadow-card);
    }

    .card-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--space-3);
      margin-bottom: var(--space-3);
    }

    .card-name {
      font-size: var(--font-size-base);
      font-weight: var(--font-weight-semibold);
      color: var(--color-text-primary);
      word-break: break-word;
    }

    .card-comment {
      font-size: var(--font-size-sm);
      color: var(--color-text-muted);
      margin-bottom: var(--space-3);
    }

    .edit-btn {
      background: none;
      border: var(--border-subtle);
      color: var(--color-text-muted);
      cursor: pointer;
      padding: var(--space-1) var(--space-2);
      border-radius: var(--radius-sm);
      font-size: var(--font-size-xs);
      font-family: var(--font-family-base);
      transition: color var(--transition-fast), background var(--transition-fast);
      flex-shrink: 0;
      display: flex;
      align-items: center;
      gap: var(--space-1);
    }
    .edit-btn:hover { color: var(--color-text-primary); background: rgba(255,255,255,0.06); }

    .config-block {
      background: var(--color-bg-base);
      border: var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: var(--space-3);
      font-family: var(--font-family-mono);
      font-size: var(--font-size-xs);
      color: var(--color-text-muted);
      overflow-x: auto;
      white-space: pre;
      max-height: 120px;
      overflow-y: auto;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 2px var(--space-2);
      background: var(--color-accent-subtle);
      color: var(--color-accent);
      border-radius: var(--radius-full);
      font-size: var(--font-size-xs);
      font-weight: var(--font-weight-medium);
    }
  </style>
  <div id="content"></div>
`;

export class ConfigList extends HTMLElement {
    #shadow: ShadowRoot;

    constructor() {
        super();
        this.#shadow = this.attachShadow({ mode: 'open' });
        this.#shadow.appendChild(template.content.cloneNode(true));
    }

    connectedCallback(): void {
        store.addEventListener('configs-changed', this.#render);
        store.addEventListener('app-selected', this.#onAppSelected);
        this.#renderConfigs(store.configs as ConfigurationResponse[]);
    }

    disconnectedCallback(): void {
        store.removeEventListener('configs-changed', this.#render);
        store.removeEventListener('app-selected', this.#onAppSelected);
    }

    #render = (e: Event): void => {
        this.#renderConfigs((e as CustomEvent<ConfigurationResponse[]>).detail);
    };

    #onAppSelected = (e: Event): void => {
        const id = (e as CustomEvent<string | null>).detail;
        if (!id) {
            this.#shadow.getElementById('content')!.innerHTML = '';
        }
    };

    #renderConfigs(configs: ConfigurationResponse[]): void {
        const container = this.#shadow.getElementById('content')!;

        if (!store.selectedAppId) {
            container.innerHTML = '';
            return;
        }

        if (configs.length === 0) {
            container.innerHTML = `
        <div class="empty">
          <div class="empty-icon">⚙️</div>
          <div class="empty-title">No configurations yet</div>
          <div class="empty-sub">Click "+ New Configuration" to add the first one.</div>
        </div>`;
            return;
        }

        container.innerHTML = `<div class="grid">${configs.map((c) => this.#renderCard(c)).join('')}</div>`;

        container.querySelectorAll('.edit-btn').forEach((btn) => {
            btn.addEventListener('click', () => {
                const id = (btn as HTMLElement).dataset['configId'];
                const config = configs.find((c) => c.id === id);
                if (config) {
                    this.dispatchEvent(new CustomEvent('edit-config', {
                        detail: config,
                        bubbles: true,
                        composed: true,
                    }));
                }
            });
        });
    }

    #renderCard(c: ConfigurationResponse): string {
        const hasConfig = Object.keys(c.config).length > 0;
        const jsonStr = hasConfig ? JSON.stringify(c.config, null, 2) : '{}';

        return `
      <div class="card">
        <div class="card-header">
          <span class="card-name">${this.#escape(c.name)}</span>
          <button class="edit-btn" data-config-id="${c.id}" aria-label="Edit ${this.#escape(c.name)}">
            <svg width="12" height="12" viewBox="0 0 14 14" fill="none">
              <path d="M9.5 1.5l3 3L4 13H1v-3L9.5 1.5z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
            </svg>
            Edit
          </button>
        </div>
        ${c.comments ? `<p class="card-comment">${this.#escape(c.comments)}</p>` : ''}
        <span class="badge">${Object.keys(c.config).length} key${Object.keys(c.config).length !== 1 ? 's' : ''}</span>
        ${hasConfig ? `<div class="config-block" style="margin-top:var(--space-3)">${this.#escape(jsonStr)}</div>` : ''}
      </div>`;
    }

    #escape(str: string): string {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
}

customElements.define('config-list', ConfigList);
