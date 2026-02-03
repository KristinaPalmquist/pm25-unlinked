const https = require('https');

// Helper function to make HTTPS requests
function httpsRequest(options, postData = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve({ statusCode: res.statusCode, body: data, headers: res.headers });
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });
    
    req.on('error', reject);
    
    if (postData) {
      req.write(postData);
    }
    
    req.end();
  });
}

// Get Hopsworks authentication token
async function getHopsworksToken(apiKey) {
  const options = {
    hostname: 'c.app.hopsworks.ai',
    path: '/api/auth/login',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const postData = JSON.stringify({ apiKey });
  
  try {
    const response = await httpsRequest(options, postData);
    const data = JSON.parse(response.body);
    return data.token;
  } catch (error) {
    throw new Error(`Hopsworks auth failed: ${error.message}`);
  }
}

// Query feature store
async function queryFeatureStore(token, projectId, query) {
  const options = {
    hostname: 'c.app.hopsworks.ai',
    path: `/api/project/${projectId}/featurestores/query`,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  };
  
  const postData = JSON.stringify(query);
  
  try {
    const response = await httpsRequest(options, postData);
    return JSON.parse(response.body);
  } catch (error) {
    throw new Error(`Feature store query failed: ${error.message}`);
  }
}

exports.handler = async function(event, context) {
  try {
    const params = event.queryStringParameters || {};
    
    // Get API key from environment
    const apiKey = process.env.HOPSWORKS_API_KEY;
    if (!apiKey) {
      return {
        statusCode: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify({ error: 'HOPSWORKS_API_KEY not configured' })
      };
    }
    
    // For now, return a helpful message explaining the situation
    if (params.type === 'predictions') {
      return {
        statusCode: 503,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify({
          error: 'Hopsworks integration temporarily unavailable',
          message: 'The predictions API requires Hopsworks Python SDK which is not available in Netlify Functions.',
          workaround: 'Generate predictions.json during build and serve as static file',
          steps: [
            '1. Run notebook 4 to generate predictions',
            '2. Export predictions to frontend/predictions.json',
            '3. Update frontend to fetch from static file instead of function'
          ]
        })
      };
    }
    
    return {
      statusCode: 400,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({ error: 'Invalid request. Use ?type=predictions' })
    };
    
  } catch (error) {
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({ error: error.message })
    };
  }
};
