export function NoAccess({ what }: { what: string }) {
  return (
    <div className="card denied">
      <b>No access.</b> Your role can't view {what}. Ask an admin if you need it.
    </div>
  );
}
