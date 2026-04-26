import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/fcm_service.dart';
import 'core/offline/offline_cache.dart';
import 'core/providers.dart';
import 'core/router.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
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
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1F77B4)),
        useMaterial3: true,
      ),
      routerConfig: router,
    );
  }
}
