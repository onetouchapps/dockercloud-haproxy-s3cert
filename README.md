# tutumcloud-haproxy-s3cert

## Links:

  - tutumcloud-haproxy-s3cert on [Docker Hub](https://hub.docker.com/r/clearreview/tutumcloud-haproxy-s3cert/)
  - tutumcloud-haproxy-s3cert on [Github](https://github.com/onetouchapps/tutumcloud-haproxy-s3cert)

## Rationale

While the [HAProxy adaptation](https://github.com/tutumcloud/haproxy) for
Tutum / Docker Cloud is excellent and effortless to implement, it does require
that for SSL termination, a private key and public cert pair are passed
through to the proxy container (or its linked services) via an environment
variable in order to be made available at runtime.
(See the [Tutum HAProxy docs](https://github.com/tutumcloud/haproxy#ssl-termination) for details.)

This is perfectly sound practice however to implement this inside a Tutum Stack,
it is probably required that you place your key/cert file (escaped) in
the Stackfile at Tutum.

One alternative to this would be to store that same key/cert file in a private
S3 bucket and to read that securely when the HAProxy container first starts.

This repo creates an image which extends the Tutum HAProxy to provide that S3-based
implmentation

## Assumptions

  - You already have a service which requires balancing
  - You will run this HAProxy derivative on an EC2 node

## Implementing this within a Tutum / Docker Cloud stack

### Stackfile additions

Add the following to the Stackfile:

```
lb:
  image: 'clearreview/tutumcloud-haproxy-s3cert'
  environment:
    CERT_BUCKET_IAM_ROLE: <IAM role name - see ("AWS setup" below)>
    CERT_BUCKET_NAME: <S3 bucket name for cert file>
    CERT_OBJECT_NAME: <S3 object name for cert file>
  links:
    - 'app:app'
  ports:
    - '80:80'
    - '443:443'
  roles:
    - global
```

#### Notes on Stackfile:

  - "links" - this will naturally contain the name of the service for which
    HAProxy is balancing the load
  - "ports" - these will vary depending on whether or not you service one of - or
    both - http and https
  - "roles" - this list **has to** contain "global" for the HAProxy container
    to have access to the Tutum API in order to be able to auto-scale in response
    to linked service containers coming online / going offline

For more info on implementing HAProxy at Tutum / Docker Cloud, see
[Tutum HAProxy docs](https://github.com/tutumcloud/haproxy#usage-within-tutum).

### AWS Setup

This implementation makes use of the AWS feature whereby an EC2 instance may
be provided securely with temporary security credentials for a particular AWS IAM role.
See the AWS docs [here](http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_use-resources.html) and [here](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html#instance-metadata-security-credentials) for more background.

#### Summary of Steps

  1. Create a cert file which contains your SSL key and the public cert, combined
  2. Upload that file to a private S3 bucket
  3. Create an IAM role with an access policy which allows access to that
     bucket
  4. Create a node cluster in Tutum / Docker Cloud which is *in that IAM role*
    (this is an option on the "Create a node cluster" dashboard screen)

#### Steps in detail

##### 1. Create a cert file

In the Tutum HAProxy docs, it is clearly explained that the environment
variable which contains the cert data needs to have its `\n` characters
escaped to `\\n`. **That is not necessary for this implementation**. The code
in this repo which collects the cert file expects it to be a standard-format
newline-delimited "pem" format file.

If for example you had two files:

  - "server.key" - the server's private key
  - "server.crt" - the server's signed, public key

then you might create such a combined cert file like this:
```
$ cp server.key cert.pem
$ cat server.crt >> cert.pem
```

#### 2. Upload that file

Upload file created in the last step ("cert.pem" in our example above).

#### 3. Create the IAM role

The access restrictions for the bucket and the uploaded file object do not
need altering. These should remain at the default "private" settings. Instead,
create a role in IAM and assign it the following policy:
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:Get*",
                "s3:List*"
            ],
            "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*"
        }
    ]
}
```

There is no need to create a user. When the "collect cert" script requests
temporary role credentials, IAM provides a working set of temporary creds with
which to access the bucket.

#### 4. Create a node / node cluster in that IAM role

"IAM role" is one of the options when creating a node in Tutum / Docker Cloud.
Creating a node in that role will mean that it can get access to temporary
credentials within that role, via the fixed link-local IP address 169.254.169.254.

It follows that any containers on that instance are also able to access that IP
address to gain temporary role credentials. Thus the container provided in this
image is able to use these temporary credentials to access the S3 bucket and download the
cert at startup.

The startup script then escapes the downloaded file (as per the Tutum HAProxy)
requirements, exports it to the `DEFAULT_SSL_CERT` environment variable and then
calls the normal entrypoint for a Tutum HAProxy container.
