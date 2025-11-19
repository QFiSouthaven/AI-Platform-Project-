import React, { useEffect, useRef } from 'react';

const QualityChart = ({
  scores = {},
  size = 300,
  showLabels = true,
  showValues = true,
  color = '#6366f1',
  backgroundColor = '#1e1e1e',
}) => {
  const canvasRef = useRef(null);

  const defaultScores = {
    readability: 0,
    performance: 0,
    maintainability: 0,
    security: 0,
    testability: 0,
    documentation: 0,
  };

  const mergedScores = { ...defaultScores, ...scores };
  const labels = Object.keys(mergedScores);
  const values = Object.values(mergedScores);
  const numAxes = labels.length;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const centerX = size / 2;
    const centerY = size / 2;
    const radius = (size / 2) - 40;

    // Clear canvas
    ctx.clearRect(0, 0, size, size);

    // Draw background
    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, size, size);

    // Draw grid circles
    const gridLevels = 5;
    for (let i = 1; i <= gridLevels; i++) {
      const levelRadius = (radius / gridLevels) * i;
      ctx.beginPath();
      ctx.strokeStyle = '#333';
      ctx.lineWidth = 1;

      for (let j = 0; j <= numAxes; j++) {
        const angle = (Math.PI * 2 * j) / numAxes - Math.PI / 2;
        const x = centerX + levelRadius * Math.cos(angle);
        const y = centerY + levelRadius * Math.sin(angle);

        if (j === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.closePath();
      ctx.stroke();
    }

    // Draw axis lines
    for (let i = 0; i < numAxes; i++) {
      const angle = (Math.PI * 2 * i) / numAxes - Math.PI / 2;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);

      ctx.beginPath();
      ctx.strokeStyle = '#444';
      ctx.lineWidth = 1;
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(x, y);
      ctx.stroke();
    }

    // Draw data polygon
    ctx.beginPath();
    for (let i = 0; i < numAxes; i++) {
      const angle = (Math.PI * 2 * i) / numAxes - Math.PI / 2;
      const value = values[i] / 100;
      const x = centerX + radius * value * Math.cos(angle);
      const y = centerY + radius * value * Math.sin(angle);

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.closePath();

    // Fill with gradient
    const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius);
    gradient.addColorStop(0, `${color}40`);
    gradient.addColorStop(1, `${color}20`);
    ctx.fillStyle = gradient;
    ctx.fill();

    // Stroke
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw data points
    for (let i = 0; i < numAxes; i++) {
      const angle = (Math.PI * 2 * i) / numAxes - Math.PI / 2;
      const value = values[i] / 100;
      const x = centerX + radius * value * Math.cos(angle);
      const y = centerY + radius * value * Math.sin(angle);

      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Draw labels
    if (showLabels) {
      ctx.font = '12px Inter, sans-serif';
      ctx.fillStyle = '#e0e0e0';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      for (let i = 0; i < numAxes; i++) {
        const angle = (Math.PI * 2 * i) / numAxes - Math.PI / 2;
        const labelRadius = radius + 25;
        const x = centerX + labelRadius * Math.cos(angle);
        const y = centerY + labelRadius * Math.sin(angle);

        const label = labels[i].charAt(0).toUpperCase() + labels[i].slice(1);
        ctx.fillText(label, x, y);

        if (showValues) {
          ctx.font = '10px Inter, sans-serif';
          ctx.fillStyle = '#888';
          ctx.fillText(`${values[i]}%`, x, y + 14);
          ctx.font = '12px Inter, sans-serif';
          ctx.fillStyle = '#e0e0e0';
        }
      }
    }
  }, [scores, size, color, backgroundColor, showLabels, showValues]);

  const averageScore = Math.round(values.reduce((a, b) => a + b, 0) / values.length);

  return (
    <div className="quality-chart-container">
      <canvas
        ref={canvasRef}
        width={size}
        height={size}
        className="quality-chart-canvas"
      />
      <div className="average-score">
        <span className="score-value">{averageScore}</span>
        <span className="score-label">Overall Score</span>
      </div>

      <style jsx>{`
        .quality-chart-container {
          position: relative;
          display: inline-block;
        }

        .quality-chart-canvas {
          display: block;
        }

        .average-score {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          text-align: center;
        }

        .score-value {
          display: block;
          font-size: 32px;
          font-weight: 700;
          color: ${color};
        }

        .score-label {
          display: block;
          font-size: 11px;
          color: #888;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
      `}</style>
    </div>
  );
};

export default QualityChart;
