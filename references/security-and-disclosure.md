# Security and disclosure guide

Use this guide to keep Boomi documentation portable and useful without
exposing credentials, private payloads, or unnecessary environment details.
Evidence-backed doesn't mean unrestricted disclosure.

## Select the audience

Identify the report audience before you copy exact values into Markdown,
manifests, SVG labels, or ImageGen input.

- Use exact component names, IDs, versions, operation names, and profile names
  when technical reviewers need them and the output remains inside its approved
  audience.
- Use generic system roles when exact environment names, tenant names, host
  names, or business partners aren't needed for the decision.
- Exclude secrets, access tokens, passwords, certificates, private keys,
  connector credentials, session values, and authentication headers.
- Redact customer, patient, employee, payment, and other sensitive payload
  values unless the requester provides explicit authority and a secure output
  destination.

## Minimize evidence

Document the claim and its evidence location without reproducing raw sensitive
content.

Prefer:

```text
Connector operation `Create Order` uses the configured target connection.
Evidence: `active-development/operations/create-order.xml`.
```

Don't paste the connection's credential values, full request payloads, or
production responses.

## Protect generated visuals

Treat manifests, SVG, raster blueprints, ImageGen prompts, generated PNGs, and
verification sidecars as documentation artifacts with the same disclosure
boundary as the report.

- Remove secrets and sensitive payload values before manifest creation.
- Don't send confidential values to ImageGen merely because they appear in
  source evidence.
- Keep necessary technical labels exact after approved redaction.
- Record a redaction as an evidence limitation when it affects interpretation.
- Don't claim the generated image preserves data that was intentionally
  excluded.

## Keep standalone HTML inert

Version 2 standalone HTML contains embedded CSS and either inline SVG or a
verified embedded PNG. It doesn't contain active or networked content.

Strict validation rejects:

- Scripts, event handlers, forms, frames, embeds, and objects.
- External stylesheets, CSS imports, and CSS URLs.
- Remote, protocol-relative, and local-file references.
- Images other than a verified PNG data URL in ImageGen mode.
- Broken anchors, duplicate IDs, unsafe URI schemes, and unresolved
  placeholders.

Don't weaken the Content Security Policy to make a report render. Fix the
artifact or omit the unsupported visual.

## Report redactions and gaps

State what you withheld and what that prevents the report from proving. Use
specific language such as:

```text
The endpoint host and example payload values were redacted for this audience.
Current connector XML establishes the operation reference, but this report
doesn't verify the target environment or runtime response.
```

This disclosure keeps a safe report decision-ready without implying evidence
that the audience can't inspect.
