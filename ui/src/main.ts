/**
 * src/main.ts
 * -----------
 * Application entry point.
 * Imports and registers all custom Web Components.
 * The root <app-shell> element is already present in index.html;
 * this module activates it by registering the component definitions.
 */

// Register all Web Components (side-effects only — each file calls customElements.define)
import './components/app-shell/app-shell.js';
