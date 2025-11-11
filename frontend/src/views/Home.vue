<template>
  <div class="home">
    <h1>Bienvenue sur l'Application Kanban</h1>
    <p>Cette application est en cours de développement.</p>
    <div class="info">
      <h2>API disponible:</h2>
      <ul>
        <li><a href="/api">/api - Informations sur l'API</a></li>
        <li><a href="/docs">/docs - Documentation interactive</a></li>
        <li><a href="/api/health">/api/health - Statut de l'API</a></li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home'
}
</script>

<style scoped>
.home {
  max-width: 800px;
  margin: 50px auto;
  padding: 20px;
  text-align: center;
}

h1 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.info {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin-top: 30px;
  text-align: left;
}

.info h2 {
  color: #42b983;
  margin-bottom: 15px;
}

.info ul {
  list-style: none;
  padding: 0;
}

.info li {
  margin: 10px 0;
}

.info a {
  color: #42b983;
  text-decoration: none;
}

.info a:hover {
  text-decoration: underline;
}
</style>
