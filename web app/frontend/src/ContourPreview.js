import React from 'react';

function ContourPreview({ image }) {
  return (
    <div>
      <h3>Processed Image Preview:</h3>
      <img src={image} alt="Processed" width="500" height="500" />
    </div>
  );
}

export default ContourPreview;
