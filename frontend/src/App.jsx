import { useState } from "react";
import BookingView from "./views/BookingView.jsx";
import MoviesView from "./views/MoviesView.jsx";
import RewatchPlanView from "./views/RewatchPlanView.jsx";

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
        {activeTab === "Movies" && <MoviesView />}
        {activeTab === "Rewatch Plan" && <RewatchPlanView />}
        {activeTab === "Booking" && <BookingView />}
      </main>
    </div>
  );
}
