const HTML_NAMESPACE = 'http://www.w3.org/1999/xhtml';
const MAX_DEPTH = 256;

const ALLOWED_TAGS = new Set([
  'a',
  'abbr',
  'b',
  'bdi',
  'bdo',
  'blockquote',
  'br',
  'caption',
  'center',
  'cite',
  'code',
  'col',
  'colgroup',
  'dd',
  'del',
  'details',
  'dfn',
  'div',
  'dl',
  'dt',
  'em',
  'figcaption',
  'figure',
  'font',
  'h1',
  'h2',
  'h3',
  'h4',
  'h5',
  'h6',
  'hr',
  'i',
  'img',
  'ins',
  'kbd',
  'li',
  'mark',
  'ol',
  'p',
  'pre',
  'q',
  's',
  'samp',
  'small',
  'span',
  'strike',
  'strong',
  'sub',
  'summary',
  'sup',
  'table',
  'tbody',
  'td',
  'tfoot',
  'th',
  'thead',
  'time',
  'tr',
  'tt',
  'u',
  'ul',
  'var',
  'wbr',
]);

// Elements whose content is not rendered as markup, or is active content, are dropped together
// with everything inside them instead of being unwrapped.
const DROPPED_WITH_CONTENT_TAGS = new Set([
  'applet',
  'audio',
  'base',
  'button',
  'canvas',
  'embed',
  'frame',
  'frameset',
  'head',
  'iframe',
  'input',
  'link',
  'math',
  'meta',
  'noembed',
  'noframes',
  'noscript',
  'object',
  'option',
  'param',
  'plaintext',
  'script',
  'select',
  'style',
  'svg',
  'template',
  'textarea',
  'title',
  'video',
  'xmp',
]);

const ALLOWED_ATTRIBUTES = new Set([
  'abbr',
  'align',
  'alt',
  'border',
  'cellpadding',
  'cellspacing',
  'class',
  'color',
  'colspan',
  'datetime',
  'dir',
  'face',
  'headers',
  'height',
  'lang',
  'nowrap',
  'open',
  'reversed',
  'rowspan',
  'scope',
  'size',
  'span',
  'start',
  'title',
  'valign',
  'width',
]);

const URL_ATTRIBUTES: {
  [tagName: string]: {
    attribute: string;
    isAllowed: (url: URL, value: string) => boolean;
  };
} = {
  a: {
    attribute: 'href',
    isAllowed: url => ['http:', 'https:', 'mailto:'].includes(url.protocol),
  },
  img: {
    attribute: 'src',
    isAllowed: (url, value) => ['http:', 'https:'].includes(url.protocol)
      || /^data:image\/(gif|jpeg|png|webp);base64,[a-z0-9+/=\s]*$/i.test(value.trim()),
  },
};

function sanitizeUrl(tagName: string, attribute: string, value: string): string | null {
  const rule = URL_ATTRIBUTES[tagName];
  if (!rule || rule.attribute !== attribute) {
    return null;
  }

  try {
    const url = new URL(value, window.location.href);
    if (rule.isAllowed(url, value)) {
      return value;
    }
  } catch {
    return null;
  }

  return null;
}

function sanitizeNode(node: Node, target: Node, doc: Document, depth: number) {
  if (node.nodeType === Node.TEXT_NODE) {
    target.appendChild(doc.createTextNode(node.textContent || ''));
    return;
  }

  if (node.nodeType !== Node.ELEMENT_NODE) {
    return;
  }

  const element = node as Element;
  const tagName = element.localName;

  if (element.namespaceURI !== HTML_NAMESPACE || DROPPED_WITH_CONTENT_TAGS.has(tagName)) {
    return;
  }

  if (depth >= MAX_DEPTH) {
    target.appendChild(doc.createTextNode(element.textContent || ''));
    return;
  }

  let container: Node = target;
  if (ALLOWED_TAGS.has(tagName)) {
    const clean = doc.createElement(tagName);

    Array.from(element.attributes).forEach(({ name, value }) => {
      const attribute = name.toLowerCase();
      if (ALLOWED_ATTRIBUTES.has(attribute)) {
        clean.setAttribute(attribute, value);
      } else {
        const url = sanitizeUrl(tagName, attribute, value);
        if (url !== null) {
          clean.setAttribute(attribute, url);
        }
      }
    });

    if (tagName === 'a' && clean.hasAttribute('href')) {
      clean.setAttribute('rel', 'noopener noreferrer nofollow');
      clean.setAttribute('target', '_blank');
    }

    target.appendChild(clean);
    container = clean;
  }

  Array.from(element.childNodes).forEach(child => sanitizeNode(child, container, doc, depth + 1));
}

// Builds new DOM nodes from untrusted HTML using an allowlist of elements and attributes.
// The markup is parsed into an inert document, so nothing in it runs or loads while it is
// inspected, and the result is a tree of freshly created nodes rather than a string, so it is
// never parsed a second time.
export function sanitizeHTML(html: string): DocumentFragment | null {
  if (typeof window === 'undefined' || typeof DOMParser === 'undefined') {
    return null;
  }

  const fragment = document.createDocumentFragment();
  const parsed = new DOMParser().parseFromString(String(html ?? ''), 'text/html');

  Array.from(parsed.body?.childNodes || [])
    .forEach(child => sanitizeNode(child, fragment, document, 0));

  return fragment;
}
