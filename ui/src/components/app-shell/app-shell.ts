/**
 * src/components/app-shell/app-shell.ts
 * --------------------------------------
 * Root layout Web Component. Provides the two-column shell:
 * a fixed sidebar (application list + add button) and a scrollable
 * main content area (configuration list + controls).
 *
 * Observed attributes: none
 * Emitted events:      none (orchestrates child components directly)
 * Store subscriptions: loading-changed, error-changed, app-selected
 */

import { store } from '../../store/app-store.js';
import '../app-list/app-list.js';
import '../app-form/app-form.js';
import '../config-list/config-list.js';
import '../config-form/config-form.js';
import '../toast-notification/toast-notification.js';

const template = document.createElement('template');
template.innerHTML = `
  <style>
    :host {
      display: flex;
      height: 100vh;
      overflow: hidden;
      background: var(--color-bg-base);
    }

    .sidebar {
      width: var(--sidebar-width, 260px);
      min-width: var(--sidebar-width, 260px);
      background: var(--color-bg-surface);
      border-right: var(--border-subtle);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .sidebar-header {
      padding: var(--space-6) var(--space-4) var(--space-4);
      border-bottom: var(--border-subtle);
      flex-shrink: 0;
    }

    .sidebar-title {
      font-size: var(--font-size-xs);
      font-weight: var(--font-weight-semibold);
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--color-text-muted);
      margin-bottom: var(--space-3);
    }

    .logo {
      font-size: var(--font-size-lg);
      font-weight: var(--font-weight-bold);
      color: var(--color-text-primary);
      display: flex;
      align-items: center;
      gap: var(--space-2);
    }

    .logo-dot {
      width: 8px;
      height: 8px;
      border-radius: var(--radius-full);
      background: var(--color-accent);
      box-shadow: 0 0 8px var(--color-accent);
    }

    .add-btn {
      width: 100%;
      margin-top: var(--space-3);
      padding: var(--space-2) var(--space-3);
      background: var(--color-accent-subtle);
      color: var(--color-accent);
      border: 1px solid rgba(108, 143, 255, 0.2);
      border-radius: var(--radius-md);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      font-family: var(--font-family-base);
      cursor: pointer;
      transition: background var(--transition-fast), border-color var(--transition-fast);
      display: flex;
      align-items: center;
      gap: var(--space-2);
    }

    .add-btn:hover {
      background: rgba(108, 143, 255, 0.2);
      border-color: rgba(108, 143, 255, 0.4);
    }

    .sidebar-content {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
    }

    .main {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      background: var(--color-bg-base);
    }

    .main-header {
      padding: var(--space-6) var(--space-8);
      border-bottom: var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
      min-height: var(--header-height, 64px);
    }

    .main-title {
      font-size: var(--font-size-xl);
      font-weight: var(--font-weight-semibold);
      color: var(--color-text-primary);
      transition: opacity var(--transition-fast);
    }

    .main-title.muted {
      color: var(--color-text-muted);
      font-weight: var(--font-weight-normal);
    }

    .add-config-btn {
      padding: var(--space-2) var(--space-4);
      background: var(--color-accent);
      color: var(--color-text-inverse);
      border: none;
      border-radius: var(--radius-md);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-semibold);
      font-family: var(--font-family-base);
      cursor: pointer;
      transition: background var(--transition-fast), transform var(--transition-fast);
      display: flex;
      align-items: center;
      gap: var(--space-2);
    }

    .add-config-btn:hover {
      background: var(--color-accent-hover);
      transform: translateY(-1px);
    }

    .add-config-btn[hidden] { display: none; }

    .main-content {
      flex: 1;
      overflow-y: auto;
      padding: var(--space-6) var(--space-8);
    }

    .loading-bar {
      height: 3px;
      background: linear-gradient(90deg, var(--color-accent), var(--color-accent-hover), var(--color-accent));
      background-size: 200% 100%;
      animation: shimmer 1.4s infinite linear;
      position: fixed;
      top: 0; left: 0; right: 0;
      z-index: 100;
      opacity: 0;
      transition: opacity var(--transition-fast);
    }

    .loading-bar.visible { opacity: 1; }

    @keyframes shimmer {
      0%   { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }

    /* Overlay for modal forms */
    .modal-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(4px);
      z-index: 50;
      align-items: center;
      justify-content: center;
    }
    .modal-overlay.open { display: flex; }
  </style>

  <div class="loading-bar" id="loadingBar"></div>

  <aside class="sidebar">
    <div class="sidebar-header">
      <span class="logo">
        <span class="logo-dot"></span>
        Config Service
      </span>
      <p class="sidebar-title" style="margin-top:var(--space-4)">Applications</p>
      <button class="add-btn" id="addAppBtn">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        New Application
      </button>
    </div>
    <div class="sidebar-content">
      <app-list id="appList"></app-list>
    </div>
  </aside>

  <main class="main">
    <div class="main-header">
      <h1 class="main-title muted" id="mainTitle">Select an application</h1>
      <button class="add-config-btn" id="addConfigBtn" hidden>
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        New Configuration
      </button>
    </div>
    <div class="main-content">
      <config-list id="configList"></config-list>
    </div>
  </main>

  <!-- App form modal -->
  <div class="modal-overlay" id="appModalOverlay">
    <app-form id="appForm"></app-form>
  </div>

  <!-- Config form modal -->
  <div class="modal-overlay" id="configModalOverlay">
    <config-form id="configForm"></config-form>
  </div>

  <toast-notification id="toast"></toast-notification>
`;

export class AppShell extends HTMLElement {
    #shadow: ShadowRoot;

    constructor() {
        super();
        this.#shadow = this.attachShadow({ mode: 'open' });
        this.#shadow.appendChild(template.content.cloneNode(true));
    }

    connectedCallback(): void {
        this.#bindEvents();
        store.addEventListener('loading-changed', this.#onLoadingChanged);
        store.addEventListener('error-changed', this.#onErrorChanged);
        store.addEventListener('app-selected', this.#onAppSelected);
        // Kick off initial data load
        void store.loadApplications();
    }

    disconnectedCallback(): void {
        store.removeEventListener('loading-changed', this.#onLoadingChanged);
        store.removeEventListener('error-changed', this.#onErrorChanged);
        store.removeEventListener('app-selected', this.#onAppSelected);
    }

    #bindEvents(): void {
        this.#shadow.getElementById('addAppBtn')!.addEventListener('click', () => {
            (this.#shadow.getElementById('appForm') as any).reset();
            this.#shadow.getElementById('appModalOverlay')!.classList.add('open');
        });

        this.#shadow.getElementById('addConfigBtn')!.addEventListener('click', () => {
            const appId = store.selectedAppId;
            if (!appId) return;
            (this.#shadow.getElementById('configForm') as any).resetForApp(appId);
            this.#shadow.getElementById('configModalOverlay')!.classList.add('open');
        });

        // Listen for form close events
        this.#shadow.getElementById('appForm')!.addEventListener('form-close', () => {
            this.#shadow.getElementById('appModalOverlay')!.classList.remove('open');
        });
        this.#shadow.getElementById('configForm')!.addEventListener('form-close', () => {
            this.#shadow.getElementById('configModalOverlay')!.classList.remove('open');
        });

        // Listen for form success — show toast
        this.#shadow.addEventListener('form-success', (e: Event) => {
            const toast = this.#shadow.getElementById('toast') as any;
            toast.show((e as CustomEvent<string>).detail, 'success');
            this.#shadow.getElementById('appModalOverlay')!.classList.remove('open');
            this.#shadow.getElementById('configModalOverlay')!.classList.remove('open');
        });

        // Config list "edit" requests
        this.#shadow.addEventListener('edit-config', (e: Event) => {
            const configForm = this.#shadow.getElementById('configForm') as any;
            configForm.loadConfig((e as CustomEvent).detail);
            this.#shadow.getElementById('configModalOverlay')!.classList.add('open');
        });

        // App list "edit" requests
        this.#shadow.addEventListener('edit-app', (e: Event) => {
            const appForm = this.#shadow.getElementById('appForm') as any;
            appForm.loadApp((e as CustomEvent).detail);
            this.#shadow.getElementById('appModalOverlay')!.classList.add('open');
        });

        // Close modals on overlay click
        this.#shadow.getElementById('appModalOverlay')!.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.#shadow.getElementById('appModalOverlay')!.classList.remove('open');
            }
        });
        this.#shadow.getElementById('configModalOverlay')!.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.#shadow.getElementById('configModalOverlay')!.classList.remove('open');
            }
        });
    }

    #onLoadingChanged = (e: Event): void => {
        const loading = (e as CustomEvent<boolean>).detail;
        this.#shadow.getElementById('loadingBar')!.classList.toggle('visible', loading);
    };

    #onErrorChanged = (e: Event): void => {
        const error = (e as CustomEvent<string | null>).detail;
        if (error) {
            const toast = this.#shadow.getElementById('toast') as any;
            toast.show(error, 'error');
        }
    };

    #onAppSelected = (e: Event): void => {
        const id = (e as CustomEvent<string | null>).detail;
        const titleEl = this.#shadow.getElementById('mainTitle')!;
        const addConfigBtn = this.#shadow.getElementById('addConfigBtn') as HTMLButtonElement;

        if (id) {
            const app = store.applications.find((a) => a.id === id);
            titleEl.textContent = app?.name ?? 'Configurations';
            titleEl.classList.remove('muted');
            addConfigBtn.hidden = false;
        } else {
            titleEl.textContent = 'Select an application';
            titleEl.classList.add('muted');
            addConfigBtn.hidden = true;
        }
    };
}

customElements.define('app-shell', AppShell);
