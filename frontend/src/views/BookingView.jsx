import { useEffect, useState } from "react";
import { createCinema, getBookingQuote, listCinemas } from "../api.js";
import ErrorMessage from "../components/ErrorMessage.jsx";
import { formatBundles } from "../format.js";

const EMPTY_FORM = { name: "", bundleSizes: "" };

function parseBundleSizes(text) {
  return text
    .split(",")
    .map((part) => part.trim())
    .filter((part) => part !== "")
    .map(Number);
}

function QuoteResult({ quote }) {
  if (!quote.possible) {
    return <p className="quote">❌ Not possible — {quote.message}</p>;
  }
  return (
    <p className="quote">
      ✅ {quote.total_bundles} bundles: {formatBundles(quote.bundles)}
    </p>
  );
}

function AddCinemaForm({ busy, onAdd }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    try {
      await onAdd({ name: form.name, bundle_sizes: parseBundleSizes(form.bundleSizes) });
      setForm(EMPTY_FORM);
    } catch (err) {
      setError(err);
    }
  }

  return (
    <>
      <ErrorMessage error={error} />
      <form onSubmit={handleSubmit}>
        <h2 className="form-title">Add a cinema</h2>
        <label>
          Name
          <input
            value={form.name}
            onChange={(event) => setField("name", event.target.value)}
            required
            maxLength={200}
          />
        </label>
        <label>
          Bundle sizes
          <input
            value={form.bundleSizes}
            onChange={(event) => setField("bundleSizes", event.target.value)}
            required
            placeholder="2, 5"
          />
        </label>
        <button type="submit" className="primary" disabled={busy}>
          Add
        </button>
      </form>
    </>
  );
}

export default function BookingView() {
  const [cinemas, setCinemas] = useState(null);
  const [cinemaId, setCinemaId] = useState("");
  const [groupSize, setGroupSize] = useState("");
  const [quote, setQuote] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    listCinemas()
      .then((list) => {
        setCinemas(list);
        if (list.length > 0) setCinemaId(String(list[0].id));
      })
      .catch(setError);
  }, []);

  function clearResult() {
    setQuote(null);
    setError(null);
  }

  function handleCinemaChange(event) {
    setCinemaId(event.target.value);
    clearResult();
  }

  function handleGroupSizeChange(event) {
    setGroupSize(event.target.value);
    clearResult();
  }

  async function handleQuote(event) {
    event.preventDefault();
    clearResult();
    setBusy(true);
    try {
      setQuote(await getBookingQuote(cinemaId, groupSize));
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  // Errors go back to AddCinemaForm, so they are shown next to it.
  async function handleAddCinema(data) {
    setBusy(true);
    try {
      const cinema = await createCinema(data);
      setCinemas(await listCinemas());
      setCinemaId(String(cinema.id));
      clearResult();
    } finally {
      setBusy(false);
    }
  }

  if (cinemas === null) {
    return error ? <ErrorMessage error={error} /> : <p>Loading…</p>;
  }

  return (
    <section>
      {cinemas.length === 0 ? (
        <p className="muted">No cinemas yet. Add one below.</p>
      ) : (
        <form className="quote-form" onSubmit={handleQuote}>
          <label>
            Cinema:
            <select value={cinemaId} onChange={handleCinemaChange} disabled={busy}>
              {cinemas.map((cinema) => (
                <option key={cinema.id} value={cinema.id}>
                  {cinema.name} (bundles: {cinema.bundle_sizes.join(", ")})
                </option>
              ))}
            </select>
          </label>
          <label>
            Group size:
            <input
              type="number"
              value={groupSize}
              onChange={handleGroupSizeChange}
              required
              min={1}
              max={10000}
              disabled={busy}
            />
          </label>
          <button type="submit" className="primary" disabled={busy}>
            Get quote
          </button>
        </form>
      )}
      <ErrorMessage error={error} />
      {quote && <QuoteResult quote={quote} />}
      <AddCinemaForm busy={busy} onAdd={handleAddCinema} />
    </section>
  );
}
