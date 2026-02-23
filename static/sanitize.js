// sanitize.js — lightweight HTML sanitizer for LLM output
// ========================================================
// Strips dangerous tags and event-handler attributes from HTML
// rendered by marked.parse() before inserting into the DOM.
//
// This is defense-in-depth on top of CSP headers.

const DANGEROUS_TAGS = /(<\s*\/?\s*(script|iframe|object|embed|form|base|meta|link|style|svg|math)[^>]*>)/gi;
const EVENT_ATTRS = /\s+on\w+\s*=\s*("[^"]*"|'[^']*'|[^\s>]*)/gi;
const JAVASCRIPT_URI = /\s+(href|src|action)\s*=\s*["']?\s*javascript\s*:/gi;

/**
 * Remove script/iframe/object tags, on* event handlers, and javascript: URIs
 * from an HTML string. Returns the cleaned HTML.
 */
export function sanitizeHTML(html) {
    if (typeof html !== 'string') return '';
    return html
        .replace(DANGEROUS_TAGS, '')
        .replace(EVENT_ATTRS, '')
        .replace(JAVASCRIPT_URI, '');
}
