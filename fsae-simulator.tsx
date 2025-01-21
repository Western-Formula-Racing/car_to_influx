import React, { useState, useRef, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Play, Pause, RotateCcw } from 'lucide-react';

const FSAESimulator = () => {
  const [isPlaying, setIsPlaying] = useState(true);
  const [data, setData] = useState([]);
  const [carPosition, setCarPosition] = useState({ x: 0, y: 0, angle: 0 });
  const animationFrame = useRef();
  const startTime = useRef(Date.now());
  const pathLength = useRef(0);
  const pathRef = useRef();

  // Track points for the race circuit (modified for smoother animation)
  const trackPath = "M150,300 C250,300 300,200 300,150 C300,50 450,50 500,150 C550,250 700,250 750,150 C800,50 900,100 900,200 C900,300 800,350 700,300 C600,250 500,300 400,350 C300,400 100,350 150,300";

  useEffect(() => {
    if (pathRef.current) {
      pathLength.current = pathRef.current.getTotalLength();
    }
  }, []);

  useEffect(() => {
    if (!isPlaying) {
      cancelAnimationFrame(animationFrame.current);
      return;
    }

    const updateSimulation = () => {
      const currentTime = Date.now();
      const elapsedTime = (currentTime - startTime.current) / 1000;
      
      // Calculate car position along the path
      const distance = (elapsedTime * 100) % pathLength.current;
      const point = pathRef.current.getPointAtLength(distance);
      
      // Calculate angle of movement for car rotation
      const nextPoint = pathRef.current.getPointAtLength(distance + 1);
      const angle = Math.atan2(nextPoint.y - point.y, nextPoint.x - point.x) * (180 / Math.PI);
      
      // Update car position
      setCarPosition({
        x: point.x,
        y: point.y,
        angle: angle
      });

      // Simulate speed and temperature based on position in track
      const speedBase = 60;
      const speedVariation = Math.sin(distance / pathLength.current * Math.PI * 2) * 20;
      const speed = speedBase + speedVariation; // 40-80 km/h

      const tempBase = 50;
      const tempVariation = Math.sin(distance / pathLength.current * Math.PI * 4) * 5;
      const batteryTemp = tempBase + tempVariation + (speed - speedBase) * 0.1; // Temperature affected by speed
      
      setData(prevData => {
        const newData = [...prevData, {
          time: elapsedTime.toFixed(1),
          speed,
          batteryTemp,
          distance: (distance / pathLength.current * 100).toFixed(1)
        }];
        return newData.slice(-50);
      });
      
      animationFrame.current = requestAnimationFrame(updateSimulation);
    };

    updateSimulation();
    return () => cancelAnimationFrame(animationFrame.current);
  }, [isPlaying]);

  const handleReset = () => {
    startTime.current = Date.now();
    setData([]);
    setCarPosition({ x: 100, y: 200, angle: 0 });
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex justify-between items-center">
            <span>FSAE Race Track Simulation</span>
            <div className="flex gap-2">
              <button 
                onClick={() => setIsPlaying(!isPlaying)}
                className="p-2 rounded-full hover:bg-gray-100"
              >
                {isPlaying ? <Pause size={24} /> : <Play size={24} />}
              </button>
              <button 
                onClick={handleReset}
                className="p-2 rounded-full hover:bg-gray-100"
              >
                <RotateCcw size={24} />
              </button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <svg 
            width="1000" 
            height="400" 
            className="border border-gray-200 rounded-lg bg-gray-50"
          >
            {/* Race Track */}
            <path
              ref={pathRef}
              d={trackPath}
              fill="none"
              stroke="#333"
              strokeWidth="40"
              strokeLinecap="round"
            />
            <path
              d={trackPath}
              fill="none"
              stroke="#666"
              strokeWidth="38"
              strokeLinecap="round"
              strokeDasharray="5,5"
            />
            
            {/* FSAE Race Car */}
            <g
              transform={`translate(${carPosition.x},${carPosition.y}) rotate(${carPosition.angle})`}
            >
              <rect
                x="-15"
                y="-10"
                width="30"
                height="20"
                rx="5"
                fill="#e11d48"
              />
              <circle cx="-10" cy="10" r="4" fill="#333" />
              <circle cx="10" cy="10" r="4" fill="#333" />
              {/* Front arrow indicator */}
              <path d="M15,-5 L22,0 L15,5" fill="none" stroke="#333" strokeWidth="2" />
            </g>
          </svg>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Speed (km/h)</CardTitle>
          </CardHeader>
          <CardContent>
            <LineChart width={400} height={200} data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" label={{ value: 'Time (s)', position: 'bottom' }} />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Line type="monotone" dataKey="speed" stroke="#e11d48" dot={false} />
            </LineChart>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Battery Temperature (°C)</CardTitle>
          </CardHeader>
          <CardContent>
            <LineChart width={400} height={200} data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" label={{ value: 'Time (s)', position: 'bottom' }} />
              <YAxis domain={[40, 60]} />
              <Tooltip />
              <Line type="monotone" dataKey="batteryTemp" stroke="#2563eb" dot={false} />
            </LineChart>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FSAESimulator;