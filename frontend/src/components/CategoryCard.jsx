function CategoryCard({ icon, name, selected }) {
  return (
    <button className="shrink-0 w-20 text-center">

      <div
        className={`w-16 h-16 mx-auto rounded-2xl flex items-center justify-center text-3xl transition ${
          selected
            ? "bg-orange-500 shadow-md"
            : "bg-orange-50"
        }`}
      >
        {icon}
      </div>

      <p
        className={`text-xs mt-2 ${
          selected
            ? "font-bold text-orange-600"
            : "font-medium text-slate-700"
        }`}
      >
        {name}
      </p>

    </button>
  );
}

export default CategoryCard;