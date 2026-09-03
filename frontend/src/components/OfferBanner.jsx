function OfferBanner() {
  return (
    <div className="rounded-2xl bg-orange-500 p-5 text-white overflow-hidden">
      <p className="text-sm font-medium text-orange-100">
        SPECIAL OFFER
      </p>

      <h2 className="text-2xl font-bold mt-1">
        50% OFF
      </h2>

      <p className="text-sm text-orange-100 mt-1">
        On your first order
      </p>

      <button className="mt-4 px-4 py-2 bg-white text-orange-600 rounded-lg text-sm font-semibold">
        Order Now
      </button>
    </div>
  );
}

export default OfferBanner;