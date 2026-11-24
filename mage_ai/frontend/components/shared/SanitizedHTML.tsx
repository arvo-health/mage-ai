import { useEffect, useRef } from 'react';

import { sanitizeHTML } from '@utils/html';

type SanitizedHTMLProps = {
  html: string;
};

function SanitizedHTML({ html }: SanitizedHTMLProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) {
      return;
    }

    const fragment = sanitizeHTML(html);
    element.textContent = '';
    if (fragment) {
      element.appendChild(fragment);
    }
  }, [html]);

  return <div ref={ref} />;
}

export default SanitizedHTML;
