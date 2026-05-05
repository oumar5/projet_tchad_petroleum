import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/auth_controller.dart';
import '../features/auth/presentation/home_screen.dart';
import '../features/auth/presentation/login_screen.dart';

class _AuthListenable extends ChangeNotifier {
  _AuthListenable(Ref ref) {
    ref.listen(authControllerProvider, (_, _) => notifyListeners());
  }
}

final routerProvider = Provider<GoRouter>((ref) {
  final listenable = _AuthListenable(ref);
  return GoRouter(
    initialLocation: '/login',
    refreshListenable: listenable,
    redirect: (context, state) {
      final auth = ref.read(authControllerProvider);
      // Pendant la restauration de session (refresh token → access token),
      // on parque tout sur /login qui affiche un splash. Sans ça, la route
      // protégée se rendrait avant que le user soit hydraté.
      if (!auth.bootstrapped) {
        return state.matchedLocation == '/login' ? null : '/login';
      }
      final goingToLogin = state.matchedLocation == '/login';
      if (!auth.isAuthenticated && !goingToLogin) return '/login';
      if (auth.isAuthenticated && goingToLogin) return '/';
      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (_, _) => const LoginScreen()),
      GoRoute(path: '/', builder: (_, _) => const HomeScreen()),
    ],
  );
});
