function ProfileCard({ name, role }) {
  return (
    <div className="flex items-center gap-4">
      <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center text-2xl shrink-0">
        👤
      </div>

      <div>
        <p className="text-sm text-slate-500">
          Welcome back
        </p>

        <h2 className="text-xl font-bold text-slate-900">
          Hello, {name} 👋
        </h2>

        <p className="text-sm text-slate-500 mt-1">
          {role}
        </p>
      </div>
    </div>
  );
}

export default ProfileCard;