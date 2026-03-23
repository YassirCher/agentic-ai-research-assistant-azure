import React from 'react';

export default function CitationTag({ source, page }) {
  // Bonus: Click opens PDF in a viewer or scrolls to page. 
  // For now, it highlights the visual tag.
  return (
    <a 
      href={`#doc-${source}-page-${page}`} 
      className="citation-tag"
      title={`Voir la page ${page} de ${source}`}
    >
      📄 {source} (p.{page})
    </a>
  );
}
