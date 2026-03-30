/**
 * src/components/toast-notification/toast-notification.ts
 * ---------------------------------------------------------
 * Animated toast overlay for success and error feedback.
 *
 * Public API:
 *   - show(message: string, type: 'success' | 'error' | 'info') — displays the toast
 *
 * Observed attributes: none
 * Emitted events:      none
 * Auto-dismisses after 4 seconds.
 */

const template = document.createElement('template');
template.innerHTML = `
  <style>
    :host { display: block; }

    .toast {
      position: fixed;
      bottom: var(--space-6);
      right: var(--space-6);
      padding: var(--space-3) var(--space-5);
      border-radius: var(--radius-md);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      color: var(--color-text-primary);
      box-shadow: var(--shadow-toast);
      display: flex;
      align-items: center;
      gap: var(--space-3);
      z-index: 9999;
      max-width: 420px;
      border: var(--border-subtle);
      transform: translateY(16px);
      opacity: 0;
      transition: transform var(--transition-normal), opacity var(--transition-normal);
      pointer-events: none;
    }

    .toast.visible {
      transform: translateY(0);
      opacity: 1;
      pointer-events: auto;
    }

    .toast.success {
      background: var(--color-bg-elevated);
      border-color: var(--color-success);
    }

    .toast.error {
      background: var(--color-bg-elevated);
      border-color: var(--color-error);
    }

    .toast.info {
      background: var(--color-bg-elevated);
      border-color: var(--color-accent);
    }

    .icon { font-size: 1.1rem; flex-shrink: 0; }

    .message { flex: 1; line-height: var(--line-height-tight); }

    .close-btn {
      background: none;
      border: none;
      color: var(--color-text-muted);
      cursor: pointer;
      padding: var(--space-1);
      border-radius: var(--radius-sm);
      font-size: 1rem;
      line-height: 1;
      flex-shrink: 0;
      transition: color var(--transition-fast);
    }

    .close-btn:hover { color: var(--color-text-primary); }
  </style>

  <div class="toast" id="toast" role="status" aria-live="polite">
    <span class="icon" id="icon">✓</span>
    <span class="message" id="message"></span>
    <button class="close-btn" id="closeBtn" aria-label="Dismiss">✕</button>
  </div>
`;

type ToastType = 'success' | 'error' | 'info';

const ICONS: Record<ToastType, string> = {
    success: '✓',
    error: '✕',
    info: 'ℹ',
};

export class ToastNotification extends HTMLElement {
    #shadow: ShadowRoot;
    #timer: ReturnType<typeof setTimeout> | null = null;

    constructor() {
        super();
        this.#shadow = this.attachShadow({ mode: 'open' });
        this.#shadow.appendChild(template.content.cloneNode(true));
    }

    connectedCallback(): void {
        this.#shadow.getElementById('closeBtn')!.addEventListener('click', () => this.#hide());
    }

    /** Show the toast with a message and type. Auto-dismisses after 4 seconds. */
    show(message: string, type: ToastType = 'info'): void {
        const toastEl = this.#shadow.getElementById('toast')!;
        const messageEl = this.#shadow.getElementById('message')!;
        const iconEl = this.#shadow.getElementById('icon')!;

        // Clear previous timer if toast is already visible
        if (this.#timer !== null) {
            clearTimeout(this.#timer);
            toastEl.classList.remove('visible');
        }

        // Update content
        messageEl.textContent = message;
        iconEl.textContent = ICONS[type];
        toastEl.className = `toast ${type}`;

        // Trigger animation in next frame
        requestAnimationFrame(() => {
            toastEl.classList.add('visible');
        });

        // Auto-dismiss after 4 seconds
        this.#timer = setTimeout(() => this.#hide(), 4000);
    }

    #hide(): void {
        const toastEl = this.#shadow.getElementById('toast')!;
        toastEl.classList.remove('visible');
        if (this.#timer !== null) {
            clearTimeout(this.#timer);
            this.#timer = null;
        }
    }
}

customElements.define('toast-notification', ToastNotification);
