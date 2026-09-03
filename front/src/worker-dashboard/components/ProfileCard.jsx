function ProfileCard({ name, role }) {
  return (
    <div>
      <h1>Hello, {name} 👋</h1>
      <p>{role}</p>
    </div>
  );
}

export default ProfileCard;