import { useState } from "react";

import OfferBanner from "../components/OfferBanner";
import CategoryCard from "../components/CategoryCard";
import RestaurantCard from "../components/RestaurantCard";
import FlowShieldWidget from "../sdk-widget/FlowShieldWidget";

function Home() {
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [search, setSearch] = useState("");

  const categories = [
    { name: "All", icon: "🍽️" },
    { name: "Pizza", icon: "🍕" },
    { name: "Burgers", icon: "🍔" },
    { name: "Biryani", icon: "🍛" },
    { name: "Healthy", icon: "🥗" },
    { name: "Desserts", icon: "🍰" }
  ];

  const restaurants = [
    {
      id: 1,
      name: "Urban Bites",
      cuisine: "Burgers • Fast Food",
      category: "Burgers",
      rating: 4.5,
      time: "25-30 min",
      price: "₹₹"
    },
    {
      id: 2,
      name: "Spice House",
      cuisine: "Indian • Biryani",
      category: "Biryani",
      rating: 4.4,
      time: "30-35 min",
      price: "₹₹"
    },
    {
      id: 3,
      name: "Green Bowl",
      cuisine: "Healthy • Salads",
      category: "Healthy",
      rating: 4.6,
      time: "20-25 min",
      price: "₹₹"
    },
    {
      id: 4,
      name: "Pizza Corner",
      cuisine: "Pizza • Italian",
      category: "Pizza",
      rating: 4.3,
      time: "25-30 min",
      price: "₹₹"
    },
    {
      id: 5,
      name: "Sweet Treats",
      cuisine: "Desserts • Bakery",
      category: "Desserts",
      rating: 4.7,
      time: "15-20 min",
      price: "₹"
    }
  ];

  const filteredRestaurants = restaurants.filter((restaurant) => {
    const matchesCategory =
      selectedCategory === "All" ||
      restaurant.category === selectedCategory;

    const searchText = search.toLowerCase();

    const matchesSearch =
      restaurant.name.toLowerCase().includes(searchText) ||
      restaurant.cuisine.toLowerCase().includes(searchText);

    return matchesCategory && matchesSearch;
  });

  return (
    <main className="pb-6">

      {/* Location */}
      <section className="px-4 pt-5">

        <p className="text-xs text-slate-500">
          Delivering to
        </p>

        <div className="flex items-center justify-between mt-1">

          <button className="flex items-center gap-1 font-semibold text-slate-900">
            📍 Bengaluru
            <span className="text-xs">
              ▼
            </span>
          </button>

          <button className="w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center">
            👤
          </button>

        </div>

      </section>

      {/* Search */}
      <section className="px-4 mt-5">

        <div className="bg-slate-100 rounded-xl px-4 py-3 flex items-center gap-3">

          <span>
            🔍
          </span>

          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search for food or restaurants"
            className="bg-transparent outline-none w-full text-sm text-slate-700 placeholder:text-slate-400"
          />

          {search && (
            <button
              onClick={() => setSearch("")}
              className="text-slate-400"
            >
              ✕
            </button>
          )}

        </div>

      </section>

      {/* Categories */}
      <section className="mt-6">

        <div className="px-4 flex items-center justify-between mb-3">

          <h2 className="text-lg font-bold text-slate-900">
            What are you craving?
          </h2>

        </div>

        <div className="flex gap-3 overflow-x-auto px-4 pb-2">

          {categories.map((category) => (

            <div
              key={category.name}
              onClick={() => setSelectedCategory(category.name)}
              className="cursor-pointer"
            >

              <CategoryCard
                icon={category.icon}
                name={category.name}
                selected={selectedCategory === category.name}
              />

            </div>

          ))}

        </div>

      </section>

      {/* Offer */}
      {!search && selectedCategory === "All" && (
        <section className="px-4 mt-6">
          <OfferBanner />
        </section>
      )}

      {/* FlowShield */}
      {!search && selectedCategory === "All" && (
  <section className="px-4 mt-7">

    <div className="flex items-center justify-between">

      <div>
        <h2 className="text-lg font-bold text-slate-900">
          Financial Safety
        </h2>

        <p className="text-sm text-slate-500 mt-1">
          Check your financial health
        </p>
      </div>

      <FlowShieldWidget workerId={1} />

    </div>

  </section>
)}

      {/* Restaurants */}
      <section className="mt-7">

        <div className="px-4 mb-3">

          <h2 className="text-lg font-bold text-slate-900">
            {search
              ? "Search Results"
              : selectedCategory === "All"
              ? "Popular Restaurants"
              : `${selectedCategory} Restaurants`}
          </h2>

          <p className="text-sm text-slate-500 mt-1">
            {filteredRestaurants.length} restaurants available
          </p>

        </div>

        <div className="space-y-3 px-4">

          {filteredRestaurants.length > 0 ? (

            filteredRestaurants.map((restaurant) => (

              <RestaurantCard
                key={restaurant.id}
                restaurant={restaurant}
              />

            ))

          ) : (

            <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center">

              <div className="text-4xl">
                🔍
              </div>

              <h3 className="font-bold text-slate-900 mt-3">
                No restaurants found
              </h3>

              <p className="text-sm text-slate-500 mt-1">
                Try another food or restaurant name.
              </p>

              <button
                onClick={() => {
                  setSearch("");
                  setSelectedCategory("All");
                }}
                className="mt-4 px-4 py-2 bg-orange-500 text-white rounded-lg text-sm font-semibold"
              >
                Show All
              </button>

            </div>

          )}

        </div>

      </section>

    </main>
  );
}

export default Home;