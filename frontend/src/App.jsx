import { useState, useEffect } from "react";

import Home from "./pages/Home";
import Search from "./pages/Search";
import WorkerDashboard from "./worker-dashboard/WorkerDashboard";

function App() {
  const [currentView, setCurrentView] = useState("home");
  const [sdkToken, setSdkToken] = useState(null);

  // Authenticate Mock Partner to get SDK Token for Worker 1
  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/v1/mock-host/get-sdk-token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        host_worker_id: "worker-1",
        occupation: "delivery_worker"
      })
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.access_token) {
          setSdkToken(data.access_token);
        }
      })
      .catch((err) => console.error("SDK Auth Failed:", err));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">

      {/* App Header */}
      <header className="sticky top-0 z-50 bg-white border-b border-slate-200">

        <div className="max-w-md mx-auto px-4 py-4 flex items-center justify-between">

          <div className="flex items-center gap-2">

            <div className="w-9 h-9 rounded-xl bg-orange-500 flex items-center justify-center text-white">
              🍴
            </div>

            <div>
              <h1 className="font-bold text-slate-900">
                FoodFlow
              </h1>

              <p className="text-xs text-slate-500">
                Food delivered fast
              </p>
            </div>

          </div>

          <button className="w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center">
            🔔
          </button>

        </div>

      </header>

      {/* Main Content */}
      <div className="max-w-md mx-auto pb-24">

        {/* Home */}
        {currentView === "home" && (
          <Home />
        )}

        {/* Search */}
        {currentView === "search" && (
          <Search />
        )}

        {/* FlowShield */}
        {currentView === "safety" && (
          <WorkerDashboard token={sdkToken} />
        )}

        {/* Cart */}
        {currentView === "cart" && (
          <div className="px-4 pt-8 text-center">

            <div className="text-5xl">
              🛒
            </div>

            <h2 className="text-xl font-bold text-slate-900 mt-4">
              Your cart is empty
            </h2>

            <p className="text-sm text-slate-500 mt-2">
              Add some delicious food to get started.
            </p>

            <button
              onClick={() => setCurrentView("home")}
              className="mt-5 px-5 py-2.5 bg-orange-500 text-white rounded-lg text-sm font-semibold"
            >
              Browse Food
            </button>

          </div>
        )}

        {/* Profile */}
        {currentView === "profile" && (
          <div className="px-4 pt-6">

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">

              {/* User */}
              <div className="flex items-center gap-4">

                <div className="w-14 h-14 rounded-full bg-orange-100 flex items-center justify-center text-2xl">
                  👤
                </div>

                <div>
                  <h2 className="text-xl font-bold text-slate-900">
                    Rahul
                  </h2>

                  <p className="text-sm text-slate-500">
                    Delivery Partner
                  </p>
                </div>

              </div>

              {/* Profile Menu */}
              <div className="mt-6 space-y-2">

                <button className="w-full text-left p-3 rounded-xl hover:bg-slate-50">
                  📦 My Orders
                </button>

                <button className="w-full text-left p-3 rounded-xl hover:bg-slate-50">
                  📍 Saved Addresses
                </button>

                <button className="w-full text-left p-3 rounded-xl hover:bg-slate-50">
                  💳 Payment Methods
                </button>

                {/* FlowShield */}
                <button
                  onClick={() => setCurrentView("safety")}
                  className="w-full text-left p-3 rounded-xl bg-blue-50 text-blue-700 font-medium"
                >
                  🛡️ FlowShield Financial Safety
                </button>

                <button className="w-full text-left p-3 rounded-xl hover:bg-slate-50">
                  ⚙️ Settings
                </button>

              </div>

            </div>

          </div>
        )}

      </div>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-slate-200">

        <div className="max-w-md mx-auto grid grid-cols-4">

          {/* Home */}
          <button
            onClick={() => setCurrentView("home")}
            className={`py-3 flex flex-col items-center gap-1 text-xs font-medium ${
              currentView === "home"
                ? "text-orange-500"
                : "text-slate-500"
            }`}
          >
            <span className="text-lg">
              🏠
            </span>

            Home
          </button>

          {/* Search */}
          <button
            onClick={() => setCurrentView("search")}
            className={`py-3 flex flex-col items-center gap-1 text-xs font-medium ${
              currentView === "search"
                ? "text-orange-500"
                : "text-slate-500"
            }`}
          >
            <span className="text-lg">
              🔍
            </span>

            Search
          </button>

          {/* Cart */}
          <button
            onClick={() => setCurrentView("cart")}
            className={`py-3 flex flex-col items-center gap-1 text-xs font-medium ${
              currentView === "cart"
                ? "text-orange-500"
                : "text-slate-500"
            }`}
          >
            <span className="text-lg">
              🛒
            </span>

            Cart
          </button>

          {/* Profile */}
          <button
            onClick={() => setCurrentView("profile")}
            className={`py-3 flex flex-col items-center gap-1 text-xs font-medium ${
              currentView === "profile"
                ? "text-orange-500"
                : "text-slate-500"
            }`}
          >
            <span className="text-lg">
              👤
            </span>

            Profile
          </button>

        </div>

      </nav>

    </div>
  );
}

export default App;