---
name: Adapter request
about: Suggest a new framework adapter
title: '[adapter] '
labels: adapter, enhancement
---

## Framework

Name and link:

## What does it do

One-sentence description of the framework.

## What structural records would the adapter surface

For example, if you're requesting a Next.js adapter:

- App Router page files (`app/**/page.tsx`)
- API routes (`app/**/route.ts`)
- Middleware
- Layout components

## Detection signatures

How would the adapter detect this framework? Import patterns, file extensions, config filenames…

## Sample project (optional)

Link to a small open-source project that uses this framework, so we can validate the adapter against real code.

## Are you willing to write it

The fastest path is a PR — see `skills/projectlens/references/adapter-sdk.md` for the SDK guide. Adapters are typically ~80-120 LOC plus tests.

- [ ] I'd like to write this myself
- [ ] I'd like someone else to write it
