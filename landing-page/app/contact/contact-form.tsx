"use client";

import { FormEvent, useState } from "react";

const supportEmail = "support@complisenseai.com";

export default function ContactForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [message, setMessage] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const subject = encodeURIComponent(`Book a Demo - ${company || "CompliSense-AI Website"}`);
    const body = encodeURIComponent(
      `Name: ${name}\nEmail: ${email}\nCompany: ${company}\n\nMessage:\n${message}`,
    );
    window.location.href = `mailto:${supportEmail}?subject=${subject}&body=${body}`;
  }

  return (
    <form className="contact-form" onSubmit={handleSubmit}>
      <div>
        <p className="section-kicker">Book Demo</p>
        <h2>Tell us what your team is trying to operationalize.</h2>
        <p>
          Use the form to prefill an email to our team. We will follow up on compliance workflows, AI governance,
          vendor reviews, and audit readiness.
        </p>
      </div>
      <div className="contact-form-grid">
        <div className="field">
          <label htmlFor="name">Name</label>
          <input id="name" value={name} onChange={(event) => setName(event.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <div className="field field-full">
          <label htmlFor="company">Company</label>
          <input id="company" value={company} onChange={(event) => setCompany(event.target.value)} required />
        </div>
        <div className="field field-full">
          <label htmlFor="message">Message</label>
          <textarea
            id="message"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            required
          />
        </div>
      </div>
      <div className="contact-actions-row">
        <button className="button button-primary" type="submit">
          Book Demo
        </button>
        <a className="button button-secondary" href={`mailto:${supportEmail}`}>
          Email Support
        </a>
      </div>
      <p className="contact-note">Support: {supportEmail}</p>
    </form>
  );
}
