<?php
// Remove plugin options. The SQLite archive and its backups are intentionally left untouched.
if ( ! defined( 'WP_UNINSTALL_PLUGIN' ) ) exit;

delete_option( 'evogt_schema_version' );
delete_option( 'evogt_media_migrated' );
delete_option( 'evogt_media_migration_log' );
delete_transient( 'evogt_all_works' );
delete_transient( 'evogt_recordings' );
delete_transient( 'evogt_schema_checked' );
delete_transient( 'evogt_admin_flash' );
