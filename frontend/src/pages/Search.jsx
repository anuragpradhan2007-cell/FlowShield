import { useState } from "react";

function Search() {
  const [search, setSearch] = useState("");

  const restaurants = [
    {
      name: "Urban Bites",
      cuisine: "Burgers • Fast Food",
      rating: 4.5,
      time: "25-30 min"
    },
    {
      name: "Spice House",
      cuisine: "Indian • Biryani",
      rating: 4.4,
      time: "30-35 min"
    },
    {
      name: "Green Bowl",
      cuisine: "Healthy • Salads",
      rating: 4.6,
      time: "20-25 min"
    },
    {
      name: "Pizza Corner",
      cuisine: "Pizza • Italian",
      rating: 4.3,
      time: "25-30 min"
    }
  ];

  const filteredRestaurants = restaurants.filter((restaurant) =>
    `${restaurant.name} ${restaurant.cuisine}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <main className="px-4 pt-5 pb-6">

      <h1 className="text-2xl font-bold text-slate-900">
        Search
      </h1>

      <p className="text-sm text-slate-500 mt-1">
        Find your favourite food or restaurant
      </p>

      {/* Search Box */}
      <div className="mt-5 bg-slate-100 rounded-xl px-4 py-3 flex items-center gap-3">
        <span>🔍</span>

        <input
          type="text"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search restaurants or food"
          className="bg-transparent outline-none w-full text-sm text-slate-700 placeholder:text-slate-400"
        />
      </div>

      {/* Categories */}
      <div className="mt-5 flex gap-2 overflow-x-auto">
        {["🍕 Pizza", "🍔 Burgers", "🍛 Biryani", "🥗 Healthy"].map(
          (category) => (
            <button
              key={category}
              className="shrink-0 px-4 py-2 rounded-full bg-white border border-slate-200 text-sm text-slate-700"
            >
              {category}
            </button>
          )
        )}
      </div>

      {/* Results */}
      <section className="mt-7">
        <h2 className="text-lg font-bold text-slate-900">
          {search ? "Search Results" : "Popular Near You"}
        </h2>

        <div className="mt-4 space-y-3">
          {filteredRestaurants.length > 0 ? (
            filteredRestaurants.map((restaurant) => (
              <div
                key={restaurant.name}
                className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm"
              >
                <div className="flex items-center gap-3">

                  <div className="w-16 h-16 rounded-xl bg-orange-50 flex items-center justify-center text-3xl shrink-0">
                    🍽️
                  </div>

                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-slate-900">
                      {restaurant.name}
                    </h3>

                    <p className="text-sm text-slate-500 mt-1">
                      {restaurant.cuisine}
                    </p>

                    <div className="flex gap-3 mt-2 text-xs text-slate-500">
                      <span className="text-green-600 font-semibold">
                        ★ {restaurant.rating}
                      </span>

                      <span>
                        {restaurant.time}
                      </span>
                    </div>
                  </div>

                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-10">
              <div className="text-4xl">
                🔍
              </div>

              <p className="font-semibold text-slate-800 mt-3">
                No restaurants found
              </p>

              <p className="text-sm text-slate-500 mt-1">
                Try searching for something else.
              </p>
            </div>
          )}
        </div>
      </section>

    </main>
  );
}

export default Search;