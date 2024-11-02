import React, { useRef, useState } from 'react';
import Webcam from 'react-webcam';
import { Button, Grid, Paper } from '@mui/material';

function CameraCapture({ onCapture, processedImage }) {
  const webcamRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState(null);

  const capture = () => {
    const imageSrc = webcamRef.current.getScreenshot();
    setCapturedImage(imageSrc);
    onCapture(imageSrc);
  };

  return (
    <div>
      <Grid container spacing={2}>
        {/* Camera Feed */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} style={{ padding: '10px' }}>
            <Webcam
              audio={false}
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              width="100%"
              height={400}
            />
            <Button
              variant="contained"
              color="primary"
              onClick={capture}
              style={{ marginTop: '10px', width: '100%' }}
            >
              Capture Image
            </Button>
          </Paper>
        </Grid>

        {/* Image Preview */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} style={{ padding: '10px', textAlign: 'center' }}>
            {processedImage ? (
              <img
                src={processedImage}
                alt="Processed"
                style={{ width: '100%', maxHeight: '400px', objectFit: 'contain' }}
              />
            ) : (
              capturedImage && (
                <img
                  src={capturedImage}
                  alt="Captured"
                  style={{ width: '100%', maxHeight: '400px', objectFit: 'contain' }}
                />
              )
            )}
          </Paper>
        </Grid>
      </Grid>
    </div>
  );
}

export default CameraCapture;
