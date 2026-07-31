import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class AppConfig {
  static const String _apiBaseUrlOverride = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  static String apiBaseUrl() {
    if (_apiBaseUrlOverride.isNotEmpty) {
      return _normalizeApiBaseUrl(_apiBaseUrlOverride);
    }

    if (kIsWeb) {
      final Uri current = Uri.base;
      final String host = current.host.isEmpty ? '127.0.0.1' : current.host;
      final String scheme = current.scheme.isEmpty ? 'http' : current.scheme;
      return Uri(
        scheme: scheme,
        host: host,
        port: 8010,
        path: '/api',
      ).toString();
    }

    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8010/api';
    }

    return 'http://127.0.0.1:8010/api';
  }

  static String backendHelpText() {
    final String suggestedUrl = apiBaseUrl();
    return 'Backend erisilemedi. API adresini kontrol et: $suggestedUrl. '
        'Gerekirse uygulamayi '
        '`--dart-define=API_BASE_URL=http://BILGISAYAR_IP:8010/api` ile baslat.';
  }

  static String _normalizeApiBaseUrl(String rawUrl) {
    final String normalized = rawUrl.trim().replaceAll(RegExp(r'/+$'), '');
    if (normalized.endsWith('/api')) {
      return normalized;
    }
    return '$normalized/api';
  }
}
