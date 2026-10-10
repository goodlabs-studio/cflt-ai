// electron-builder afterSign hook: notarize the signed .app with Apple.
//
// Gracefully no-ops when:
//   - The build target is not macOS
//   - APPLE_ID / APPLE_APP_SPECIFIC_PASSWORD / APPLE_TEAM_ID are not all set
//     (this is the common case for local dev builds)
//
// In CI, set all three secrets and the hook submits the notarization
// request via @electron/notarize, blocking until the bundle is stapled.

const path = require('node:path');

module.exports = async function notarizing(context) {
  const { electronPlatformName, appOutDir, packager } = context;

  if (electronPlatformName !== 'darwin') return;

  const { APPLE_ID, APPLE_APP_SPECIFIC_PASSWORD, APPLE_TEAM_ID } = process.env;
  if (!APPLE_ID || !APPLE_APP_SPECIFIC_PASSWORD || !APPLE_TEAM_ID) {
    console.log(
      '[notarize] APPLE_ID / APPLE_APP_SPECIFIC_PASSWORD / APPLE_TEAM_ID ' +
        'not all set — skipping notarization (unsigned dev build).',
    );
    return;
  }

  // Lazy-require so dev installs don't pay the dependency cost.
  const { notarize } = require('@electron/notarize');

  const appName = packager.appInfo.productFilename;
  const appPath = path.join(appOutDir, `${appName}.app`);

  console.log(`[notarize] submitting ${appPath} to Apple…`);
  await notarize({
    tool: 'notarytool',
    appPath,
    appleId: APPLE_ID,
    appleIdPassword: APPLE_APP_SPECIFIC_PASSWORD,
    teamId: APPLE_TEAM_ID,
  });
  console.log('[notarize] notarization complete and stapled.');
};
