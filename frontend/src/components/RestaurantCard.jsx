function RestaurantCard({ restaurant }) {
  return (
    <button className="w-full text-left bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">

      <div className="h-32 bg-slate-200 flex items-center justify-center text-5xl">
        🍽️
      </div>

      <div className="p-4">
        <div className="flex items-start justify-between gap-3">

          <div>
            <h3 className="font-bold text-slate-900">
              {restaurant.name}
            </h3>

            <p className="text-sm text-slate-500 mt-1">
              {restaurant.cuisine}
            </p>
          </div>

          <span className="shrink-0 px-2 py-1 rounded-md bg-green-100 text-green-700 text-xs font-semibold">
            ★ {restaurant.rating}
          </span>

        </div>

        <div className="flex items-center gap-3 mt-3 text-xs text-slate-500">
          <span>{restaurant.time}</span>
          <span>•</span>
          <span>{restaurant.price}</span>
        </div>
      </div>

    </button>
  );
}

export default RestaurantCard;