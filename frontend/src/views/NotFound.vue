<template>
  <div class="not-found">
    <h1>404</h1>
    <p>Page non trouvée</p>
    <router-link to="/">Retour à l'accueil</router-link>
  </div>
</template>

<script>
export default {
  name: 'NotFound'
}
</script>

<style scoped>
.not-found {
  text-align: center;
  margin-top: 100px;
}

h1 {
  font-size: 72px;
  color: #e74c3c;
  margin-bottom: 20px;
}

p {
  font-size: 24px;
  color: #7f8c8d;
  margin-bottom: 30px;
}

a {
  color: #3498db;
  text-decoration: none;
  font-size: 18px;
}

a:hover {
  text-decoration: underline;
}
</style>
