import { useState } from "react";
import MoviesView from "./views/MoviesView.jsx";

const TABS = ["Movies", "Rewatch Plan", "Booking"];

export default function App() {
  const [activeTab, setActiveTab] = useState(TABS[0]);

  return (
    <div className="app">
      <header>
        <h1>Doomsday Ready</h1>
        <nav className="tabs">
          {TABS.map((tab) => (
            <button
              key={tab}
              type="button"
              className={tab === activeTab ? "tab active" : "tab"}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </nav>
      </header>
      <main>
        {activeTab === "Movies" ? (
          <MoviesView />
        ) : (
          <p className="placeholder">The {activeTab} view is coming soon.</p>
        )}
      </main>
    </div>
  );
}
