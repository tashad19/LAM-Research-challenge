import React, { useState } from 'react';
import CameraCapture from './CameraCapture';
import ContourPreview from './ContourPreview';
import axios from 'axios';
import {
  Container,
  Typography,
  Box,
  Grid,
  Button,
  TextField,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';

function App() {
  const [image, setImage] = useState(null);
  const [processedImage, setProcessedImage] = useState(null);
  const [contour, setContour] = useState(null);
  const [parameters, setParameters] = useState({
    thresholdValue: 245,
    smoothingFactor: 0.001,
    curvinessFactor: 100000,
    pixelsPerMm: 1,
    scaleFactor: 0.002,
  });

  const handleCapture = (capturedImage) => {
    setImage(capturedImage);
    setProcessedImage(null); // Reset processed image when a new capture is taken
  };

  const handleProcessImage = async () => {
    if (!image) return;
    try {
      const response = await axios.post('http://localhost:5000/process-image', {
        image: image.split(',')[1], // Remove the data URL prefix
        ...parameters,
      });
      setProcessedImage(`data:image/jpeg;base64,${response.data.processedImage}`);
      setContour(response.data.contour);
    } catch (error) {
      alert('Error processing image: ' + error.message);
    }
  };

  const handleExportDXF = async () => {
    if (!contour) return;
    try {
      const response = await axios.post(
        'http://localhost:5000/export-dxf',
        {
          contour: contour,
          pixelsPerMm: parameters.pixelsPerMm,
          scaleFactor: parameters.scaleFactor,
        },
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'contour_output.dxf');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      alert('Error exporting DXF: ' + error.message);
    }
  };

  return (
    <Container maxWidth="lg" style={{ marginTop: '20px', marginBottom: '40px' }}>
      <Typography variant="h4" align="center" gutterBottom>
        Contour Capture System
      </Typography>
      <Paper elevation={3} style={{ padding: '20px', marginBottom: '20px' }}>
        <CameraCapture onCapture={handleCapture} processedImage={processedImage} />
      </Paper>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Typography variant="h6">Parameters</Typography>
          <Box component="form" noValidate autoComplete="off">
            <TextField
              label={
                <>
                  Threshold Value (0 - 255)
                  <Tooltip title="Determines the intensity threshold for contour detection. Higher values make the detection more sensitive to bright areas.">
                    <IconButton size="small">
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </>
              }
              type="number"
              fullWidth
              variant="outlined"
              margin="normal"
              value={parameters.thresholdValue}
              onChange={(e) =>
                setParameters({ ...parameters, thresholdValue: parseInt(e.target.value) })
              }
            />
            <TextField
              label={
                <>
                  Smoothing Factor (0.01 - 0.0001)
                  <Tooltip title="Controls how much the contour is simplified and smoothed. Smaller values result in a smoother contour.">
                    <IconButton size="small">
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </>
              }
              type="number"
              fullWidth
              variant="outlined"
              margin="normal"
              step="0.0001"
              value={parameters.smoothingFactor}
              onChange={(e) =>
                setParameters({ ...parameters, smoothingFactor: parseFloat(e.target.value) })
              }
            />
            <TextField
              label={
                <>
                  Curviness Factor (0 - 100000)
                  <Tooltip title="Affects the curviness of the smoothed contour. Higher values create smoother curves.">
                    <IconButton size="small">
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </>
              }
              type="number"
              fullWidth
              variant="outlined"
              margin="normal"
              value={parameters.curvinessFactor}
              onChange={(e) =>
                setParameters({ ...parameters, curvinessFactor: parseInt(e.target.value) })
              }
            />
            <TextField
              label={
                <>
                  Pixels per mm (0.1 - 10)
                  <Tooltip title="Defines the pixel density per millimeter for exporting contours. Adjust based on the precision of your application.">
                    <IconButton size="small">
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </>
              }
              type="number"
              fullWidth
              variant="outlined"
              margin="normal"
              value={parameters.pixelsPerMm}
              onChange={(e) =>
                setParameters({ ...parameters, pixelsPerMm: parseFloat(e.target.value) })
              }
            />
            <TextField
              label={
                <>
                  Scale Factor (0.001 - 0.1)
                  <Tooltip title="Sets the scale factor for the contour when exporting to DXF. Useful for resizing the output.">
                    <IconButton size="small">
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </>
              }
              type="number"
              fullWidth
              variant="outlined"
              margin="normal"
              value={parameters.scaleFactor}
              onChange={(e) =>
                setParameters({ ...parameters, scaleFactor: parseFloat(e.target.value) })
              }
            />
          </Box>
        </Grid>

        <Grid item xs={12} md={6}>
          <Button
            variant="contained"
            color="primary"
            fullWidth
            onClick={handleProcessImage}
            style={{ marginBottom: '20px' }}
          >
            Process Image
          </Button>
          <Button
            variant="contained"
            color="secondary"
            fullWidth
            onClick={handleExportDXF}
          >
            Export DXF
          </Button>
        </Grid>
      </Grid>

      {/* Footer Section */}
      <Box
        component="footer"
        sx={{
          marginTop: '40px',
          padding: '20px',
          textAlign: 'center',
          backgroundColor: '#f5f5f5',
          borderTop: '1px solid #ddd',
        }}
      >
        <Typography variant="subtitle2">
          Copyright &copy; 2024 HX Techies | All Rights Reserved
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Developed by Tashadur Rahman
        </Typography>
      </Box>
    </Container>
  );
}

export default App;
