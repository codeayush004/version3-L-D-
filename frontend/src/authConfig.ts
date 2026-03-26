import { PublicClientApplication } from "@azure/msal-browser";
import type { Configuration } from "@azure/msal-browser";

export const msalConfig: Configuration = {
    auth: {
        clientId: "7c7d51e4-7760-47b9-8fdd-20227453f79e",
        authority: "https://login.microsoftonline.com/4ac50105-0c66-404e-a107-7cbd8a9a6442",
        redirectUri: "/",
        postLogoutRedirectUri: "/"
    },
    cache: {
        cacheLocation: "sessionStorage"
    }
};

export const loginRequest = {
    scopes: ["User.Read"]
};

export const msalInstance = new PublicClientApplication(msalConfig);
