import React from 'react';
import { api } from '../../api/client';

interface PdfReaderProps {
  bookId: number;
}

export const PdfReader: React.FC<PdfReaderProps> = ({ bookId }) => {
  const pdfUrl = `${api.getBookDownloadUrl(bookId, 'PDF')}#toolbar=1&navpanes=1`;

  return (
    <div style={{ width: '100%', height: '100%', background: '#1e293b' }}>
      <iframe
        src={pdfUrl}
        title="PDF Book Reader"
        style={{
          width: '100%',
          height: '100%',
          border: 'none',
        }}
      />
    </div>
  );
};
