import { useEffect, useState } from "react";
import { createMovie, listMovies, updateMovie } from "../api.js";
import ErrorMessage from "../components/ErrorMessage.jsx";
import { formatMinutes } from "../format.js";

const EMPTY_FORM = {
  title: "",
  releaseYear: "",
  runtimeMinutes: "",
  watched: false,
  prerequisites: [],
};

function toggleId(ids, id) {
  return ids.includes(id) ? ids.filter((other) => other !== id) : [...ids, id];
}

function PrerequisiteCheckboxes({ movies, selected, onChange, disabled }) {
  if (movies.length === 0) {
    return <span className="muted">No movies to choose from.</span>;
  }
  return (
    <div className="checkbox-list">
      {movies.map((movie) => (
        <label key={movie.id}>
          <input
            type="checkbox"
            checked={selected.includes(movie.id)}
            onChange={() => onChange(toggleId(selected, movie.id))}
            disabled={disabled}
          />
          {movie.title}
        </label>
      ))}
    </div>
  );
}

function AddMovieForm({ movies, busy, onAdd }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    try {
      await onAdd({
        title: form.title,
        release_year: Number(form.releaseYear),
        runtime_minutes: Number(form.runtimeMinutes),
        watched: form.watched,
        prerequisites: form.prerequisites,
      });
      setForm(EMPTY_FORM);
    } catch (err) {
      setError(err);
    }
  }

  return (
    <>
      <ErrorMessage error={error} />
      <form onSubmit={handleSubmit}>
        <h2 className="form-title">Add a movie</h2>
        <label>
          Title
          <input
            value={form.title}
            onChange={(event) => setField("title", event.target.value)}
            required
            maxLength={200}
          />
        </label>
        <label>
          Year
          <input
            type="number"
            value={form.releaseYear}
            onChange={(event) => setField("releaseYear", event.target.value)}
            required
            min={1900}
            max={2100}
          />
        </label>
        <label>
          Runtime (min)
          <input
            type="number"
            value={form.runtimeMinutes}
            onChange={(event) => setField("runtimeMinutes", event.target.value)}
            required
            min={1}
            max={300}
          />
        </label>
        <div className="full-width">
          Watch first:
          <PrerequisiteCheckboxes
            movies={movies}
            selected={form.prerequisites}
            onChange={(ids) => setField("prerequisites", ids)}
            disabled={busy}
          />
        </div>
        <label>
          <input
            type="checkbox"
            checked={form.watched}
            onChange={(event) => setField("watched", event.target.checked)}
            disabled={busy}
          />
          Already watched
        </label>
        <button type="submit" className="primary" disabled={busy}>
          Add movie
        </button>
      </form>
    </>
  );
}

function MovieRow({
  movie,
  movies,
  titleById,
  editing,
  editError,
  busy,
  onToggleWatched,
  onEdit,
  onEditChange,
  onSave,
  onCancel,
}) {
  const prerequisiteTitles = movie.prerequisites.map((id) => titleById.get(id)).join(", ");

  return (
    <>
      <tr>
        <td>{movie.title}</td>
        <td>{movie.release_year}</td>
        <td>{formatMinutes(movie.runtime_minutes)}</td>
        <td>
          <input
            type="checkbox"
            aria-label={`Watched ${movie.title}`}
            checked={movie.watched}
            onChange={() => onToggleWatched(movie)}
            disabled={busy}
          />
        </td>
        <td>{prerequisiteTitles || "—"}</td>
        <td>
          <button type="button" onClick={() => onEdit(movie)} disabled={busy}>
            Edit
          </button>
        </td>
      </tr>
      {editing && (
        <tr className="edit-row">
          <td colSpan={6}>
            <ErrorMessage error={editError} />
            <p className="edit-title">Watch first:</p>
            <PrerequisiteCheckboxes
              movies={movies.filter((other) => other.id !== movie.id)}
              selected={editing.prerequisites}
              onChange={onEditChange}
              disabled={busy}
            />
            <div className="actions">
              <button type="button" className="primary" onClick={onSave} disabled={busy}>
                Save
              </button>
              <button type="button" onClick={onCancel} disabled={busy}>
                Cancel
              </button>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export default function MoviesView() {
  const [movies, setMovies] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState(null);
  const [editError, setEditError] = useState(null);

  useEffect(() => {
    listMovies().then(setMovies).catch(setError);
  }, []);

  // Runs one change, then reloads the list. Errors go back to the caller,
  // so each one can be shown next to the control that caused it.
  async function saveAndReload(action) {
    setBusy(true);
    try {
      await action();
      setMovies(await listMovies());
    } finally {
      setBusy(false);
    }
  }

  async function handleToggleWatched(movie) {
    setError(null);
    try {
      await saveAndReload(() => updateMovie(movie.id, { watched: !movie.watched }));
    } catch (err) {
      setError(err);
    }
  }

  function handleEdit(movie) {
    setEditing({ movieId: movie.id, prerequisites: movie.prerequisites });
    setEditError(null);
  }

  function handleCancel() {
    setEditing(null);
    setEditError(null);
  }

  async function handleSave() {
    setEditError(null);
    try {
      await saveAndReload(() => updateMovie(editing.movieId, { prerequisites: editing.prerequisites }));
      setEditing(null);
    } catch (err) {
      setEditError(err);
    }
  }

  if (movies === null) {
    return error ? <ErrorMessage error={error} /> : <p>Loading…</p>;
  }

  const titleById = new Map(movies.map((movie) => [movie.id, movie.title]));

  return (
    <section>
      <AddMovieForm
        movies={movies}
        busy={busy}
        onAdd={(data) => saveAndReload(() => createMovie(data))}
      />
      <ErrorMessage error={error} />
      {movies.length === 0 ? (
        <p className="muted">No movies yet. Add one above.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Year</th>
                <th>Runtime</th>
                <th>Watched</th>
                <th>Watch first</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {movies.map((movie) => (
                <MovieRow
                  key={movie.id}
                  movie={movie}
                  movies={movies}
                  titleById={titleById}
                  editing={editing?.movieId === movie.id ? editing : null}
                  editError={editError}
                  busy={busy}
                  onToggleWatched={handleToggleWatched}
                  onEdit={handleEdit}
                  onEditChange={(ids) => setEditing({ ...editing, prerequisites: ids })}
                  onSave={handleSave}
                  onCancel={handleCancel}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
