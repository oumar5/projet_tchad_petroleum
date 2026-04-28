import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:intl/date_symbol_data_local.dart';

import 'core/fcm_service.dart';
import 'core/offline/offline_cache.dart';
import 'core/providers.dart';
import 'core/router.dart';
import 'core/theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting('fr_FR');
  await OfflineCache.instance.init();
  runApp(const ProviderScope(child: SmartBarrelApp()));
}

class SmartBarrelApp extends ConsumerStatefulWidget {
  const SmartBarrelApp({super.key});

  @override
  ConsumerState<SmartBarrelApp> createState() => _SmartBarrelAppState();
}

class _SmartBarrelAppState extends ConsumerState<SmartBarrelApp> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      FcmService(ref.read(apiClientProvider)).init();
    });
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'SmartBarrel',
      debugShowCheckedModeBanner: false,
      theme: buildLightTheme(),
      darkTheme: buildDarkTheme(),
      themeMode: ThemeMode.system,
      routerConfig: router,
    );
  }
}
