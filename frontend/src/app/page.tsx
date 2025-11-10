import Map from './components/map';

export default function Home() {
  return (
    <div className="relative h-screen w-full">
      <Map />
      <div className="bg-foreground/30 absolute top-4 left-4 z-10 max-w-[400px] rounded-lg px-4 py-2 backdrop-blur-sm select-none">
        <h1 className="text-background font-mono text-xl">Air Quality Forecast</h1>
        <p className="text-background/70 font-mono text-xs">Forecast for the next seven days.</p>
      </div>
    </div>
  );
}
