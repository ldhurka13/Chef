import React from "react";

const FilmGrain = () => {
  return (
    <div 
      className="fixed inset-0 pointer-events-none z-[100] opacity-[0.03] mix-blend-overlay"
      style={{
        backgroundImage: "url('https://grainy-gradients.vercel.app/noise.svg')",
        backgroundRepeat: "repeat",
      }}
      aria-hidden="true"
    />
  );
};

export default FilmGrain;
