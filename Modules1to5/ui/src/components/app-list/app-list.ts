/**
 * src/components/app-list/app-list.ts
 * ------------------------------------
 * Renders the sidebar list of all applications.
 *
 * Observed attributes: none
 * Emitted events (bubble + composed):
 *   - 'edit-app'  →  detail: ApplicationResponse  (user clicked edit icon)
 * Store subscriptions: applications-changed, app-selected
 */

import { store } from '../../store/app-store.js';
import type { ApplicationResponse } from '../../api/types.js';

const template = document.createElement('template');
template.innerHTML = `
  <style>
    :host { display: block; }

    .list { list-style: none; padding: var(--space-2) 0; }

    .item {
      display: flex;
      align-items: center;
      gap: var(--space-2);
      padding: var(--space-2) var(--space-4);
      cursor: pointer;
      color: var(--color-text-muted);
      font-size: var(--font-size-sm);
      transition: background var(--transition-fast), color var(--transition-fast);
      border-radius: 0;
      position: relative;
    }

    .item:hover { background: rgba(255,255,255,0.04); color: var(--color-text-primary); }

    .item.selected {
      background: var(--color-accent-subtle);
      color: var(--color-accent);
    }

    .item.selected::before {
      content: '';
      position: absolute;
      left: 0; top: 0; bottom: 0;
      width: 3px;
      background: var(--color-accent);
      border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    }

    .item-name {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-weight: var(--font-weight-medium);
    }

    .edit-btn {
      display: none;
      background: none;
      border: none;
      color: var(--color-text-muted);
      cursor: pointer;
      padding: var(--space-1);
      border-radius: var(--radius-sm);
      transition: color var(--transition-fast), background var(--transition-fast);
      flex-shrink: 0;
    }

    .item:hover .edit-btn, .item.selected .edit-btn { display: flex; align-items: center; }
    .edit-btn:hover { color: var(--color-text-primary); background: rgba(255,255,255,0.08); }

    .empty {
      padding: var(--space-6) var(--space-4);
      color: var(--color-text-muted);
      font-size: var(--font-size-sm);
      text-align: center;
    }
  </style>
  <ul class="list" id="list" role="listbox" aria-label="Applications"></ul>
`;

export class AppList extends HTMLElement {
    #shadow: ShadowRoot;

    constructor() {
        super();
        this.#shadow = this.attachShadow({ mode: 'open' });
        this.#shadow.appendChild(template.content.cloneNode(true));
    }

    connectedCallback(): void {
        store.addEventListener('applications-changed', this.#render);
        store.addEventListener('app-selected', this.#updateSelected);
        this.#renderList(store.applications as ApplicationResponse[]);
    }

    disconnectedCallback(): void {
        store.removeEventListener('applications-changed', this.#render);
        store.removeEventListener('app-selected', this.#updateSelected);
    }

    #render = (e: Event): void => {
        this.#renderList((e as CustomEvent<ApplicationResponse[]>).detail);
    };

    #renderList(apps: ApplicationResponse[]): void {
        const list = this.#shadow.getElementById('list')!;
        if (apps.length === 0) {
            list.innerHTML = '<li class="empty">No applications yet.<br/>Click "+ New Application" to add one.</li>';
            return;
        }
        list.innerHTML = apps.map((app) => `
      <li class="item ${app.id === store.selectedAppId ? 'selected' : ''}"
          role="option"
          aria-selected="${app.id === store.selectedAppId}"
          data-id="${app.id}">
        <span class="item-name">${this.#escape(app.name)}</span>
        <button class="edit-btn" data-edit-id="${app.id}" aria-label="Edit ${this.#escape(app.name)}">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M9.5 1.5l3 3L4 13H1v-3L9.5 1.5z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
          </svg>
        </button>
      </li>
    `).join('');

        list.querySelectorAll('.item').forEach((li) => {
            li.addEventListener('click', (e) => {
                const target = e.target as HTMLElement;
                if (target.closest('.edit-btn')) return;
                const id = (li as HTMLElement).dataset['id'];
                if (id) store.selectApplication(id);
            });
        });

        list.querySelectorAll('.edit-btn').forEach((btn) => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = (btn as HTMLElement).dataset['editId'];
                const app = store.applications.find((a) => a.id === id);
                if (app) {
                    this.dispatchEvent(new CustomEvent('edit-app', {
                        detail: app,
                        bubbles: true,
                        composed: true,
                    }));
                }
            });
        });
    }

    #updateSelected = (): void => {
        this.#renderList(store.applications as ApplicationResponse[]);
    };

    #escape(str: string): string {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
}

customElements.define('app-list', AppList);
