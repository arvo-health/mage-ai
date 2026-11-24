import Cookies from 'js-cookie';
import jwtDecode from 'jwt-decode';

import {
  COOKIE_DOMAIN,
  COOKIE_KEY_REF as COOKIE_KEY_REF_ORIG,
  COOKIE_PATH,
  SHARED_COOKIE_PROPERTIES,
} from '@utils/cookies/constants';

// The session token is set by the server in an HttpOnly cookie under this key, so page scripts
// can't read it. API requests and websocket connections are authenticated with that cookie.
export const COOKIE_KEY: string = 'oauth_token';
// Only the session's expiry is kept where the frontend can read it.
export const COOKIE_KEY_EXPIRES: string = 'oauth_token_expires';
export const COOKIE_KEY_REF: string = COOKIE_KEY_REF_ORIG;
export const DOMAIN: string = COOKIE_DOMAIN;
export const PATH: string = COOKIE_PATH;
export const SHARED_OPTS: any = SHARED_COOKIE_PROPERTIES;

// Only returns a value for a session cookie written by an older frontend, before the server
// started setting it as HttpOnly.
export function getToken(): string | undefined {
  return Cookies.get(COOKIE_KEY);
}

export function getTokenExpires(): number | undefined {
  const expires = Number(Cookies.get(COOKIE_KEY_EXPIRES));

  return expires > 0 ? expires : undefined;
}

export function removeToken(basePath?: string) {
  const opts = {
    ...SHARED_OPTS,
    path: basePath || PATH,
  };

  Cookies.remove(COOKIE_KEY, opts);
  Cookies.remove(COOKIE_KEY_EXPIRES, opts);
}

export function setToken(
  token: string,
  basePath?: string,
) {
  let expires: number;
  try {
    expires = Number(jwtDecode<{ expires: number }>(token)?.expires);
  } catch {
    return;
  }

  if (!(expires > 0)) {
    return;
  }

  Cookies.set(
    COOKIE_KEY_EXPIRES,
    String(expires),
    {
      ...SHARED_OPTS,
      expires: new Date(expires * 1000),
      path: basePath || PATH,
    },
  );
}
