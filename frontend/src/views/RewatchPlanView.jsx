import { useEffect, useState } from "react";
import { getRewatchOrder, listMovies, updateMovie } from "../api.js";
import ErrorMessage from "../components/ErrorMessage.jsx";
import { formatMinutes } from "../format.js";

function PlanItem({ movie, busy, onToggleWatched }) {
  return (
    <li className={movie.watched ? "watched" : undefined}>
      <label>
        <input
          type="checkbox"
          checked={movie.watched}
          onChange={() => onToggleWatched(movie)}
          disabled={busy}
        />
        {movie.title} ({movie.release_year}) · {formatMinutes(movie.runtime_minutes)}
      </label>
    </li>
  );
}

function Plan({ plan, busy, onToggleWatched }) {
  if (plan.total_count === 0) {
    return <p className="muted">Nothing to watch first — you're ready!</p>;
  }

  return (
    <>
      <div className="plan-summary">
        <span>
          {plan.watched_count} of {plan.total_count} watched
        </span>
        <progress value={plan.watched_count} max={plan.total_count} />
        <span>Remaining: {formatMinutes(plan.unwatched_runtime_minutes)}</span>
      </div>
      {plan.watched_count === plan.total_count && (
        <p className="muted">All caught up — you're ready!</p>
      )}
      <ol className="plan-list">
        {plan.movies.map((movie) => (
          <PlanItem
            key={movie.id}
            movie={movie}
            busy={busy}
            onToggleWatched={onToggleWatched}
          />
        ))}
      </ol>
    </>
  );
}

export default function RewatchPlanView() {
  const [movies, setMovies] = useState(null);
  const [targetId, setTargetId] = useState("");
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    listMovies().then(setMovies).catch(setError);
  }, []);

  useEffect(() => {
    if (!targetId) {
      return;
    }
    // Ignore a late answer for a movie that is no longer selected.
    let ignore = false;
    getRewatchOrder(targetId)
      .then((result) => {
        if (!ignore) setPlan(result);
      })
      .catch((err) => {
        if (!ignore) setError(err);
      });
    return () => {
      ignore = true;
    };
  }, [targetId]);

  function handleTargetChange(event) {
    setTargetId(event.target.value);
    setPlan(null);
    setError(null);
  }

  async function handleToggleWatched(movie) {
    setError(null);
    setBusy(true);
    try {
      await updateMovie(movie.id, { watched: !movie.watched });
      setPlan(await getRewatchOrder(targetId));
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  if (movies === null) {
    return error ? <ErrorMessage error={error} /> : <p>Loading…</p>;
  }

  return (
    <section>
      <label className="target-picker">
        Target movie:
        <select value={targetId} onChange={handleTargetChange} disabled={busy}>
          <option value="">Choose a movie…</option>
          {movies.map((movie) => (
            <option key={movie.id} value={movie.id}>
              {movie.title}
            </option>
          ))}
        </select>
      </label>
      <ErrorMessage error={error} />
      {!targetId && <p className="muted">Pick a movie to see what to watch first.</p>}
      {targetId && !plan && !error && <p>Loading…</p>}
      {plan && <Plan plan={plan} busy={busy} onToggleWatched={handleToggleWatched} />}
    </section>
  );
}
