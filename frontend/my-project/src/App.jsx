import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl overflow-hidden p-8 text-center space-y-6 border border-slate-200">
        
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-2">
          <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
          </svg>
        </div>

        <h1 className="text-3xl font-extrabold text-slate-800 tracking-tight">
          Tailwind is Active!
        </h1>
        
        <p className="text-slate-600 text-base">
          If this card is centered with a nice shadow, rounded corners, and colored text, your Vite + Tailwind setup is working perfectly.
        </p>
        
        <button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 transform hover:-translate-y-1 focus:outline-none focus:ring-4 focus:ring-indigo-300">
          Hover Me
        </button>
        
      </div>
    </div>
  );
}

export default App;